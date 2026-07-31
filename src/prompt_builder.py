import json
import pandas as pd

# "Statement Type" closed vocabulary, verbatim from guideline.pdf §3.1. Also
# hard-enforced via the response_schema enum below — prompt wording alone
# let the model drift to "regulative", which is not a valid cell value.
STATEMENT_TYPE_VALUES = ["choice", "boundary", "aggregation", "information", "scope", "payoff", "constitutiva"]

# json_batches/all_examples.json (sourced from data.csv) uses a slightly
# different header vocabulary than categories.csv, which drives the actual
# schema (e.g. "Type of rule" vs "Statement Type"). Rename on render so the
# few-shot examples use the same field names the model must output.
EXAMPLE_FIELD_RENAMES = {
    "Type of rule": "Statement Type",
    "Function": "Constituting Function",
    "Activation Condition (Content).1": "Activation Condition (Content)",
    "Activation Condition (Reference to Statement)": "Activation Condition (Reference to statement)",
    "Execution Constraint (Content).1": "Execution Constraint (Content)",
    "Execution Constraint (Reference to Statement)": "Execution Constraint (Reference to statement)",
    "Or else (Reference to consequential statement)": "Or else",
    "Or else (Forward reference to consequential statement)": "Or else (Forward reference)",
    "Logical combination.1": "Logical combination",
    "Invoking statement(s).1": "Invoking statement(s)",
}
EXAMPLE_FIELD_DROP = {"Modal", "Statement No."}  # spreadsheet leftovers with no schema counterpart


def clean_json_response(text_response):
    """Removes Markdown fencing if the model wraps the JSON in ```."""
    text_response = text_response.strip()
    if text_response.startswith("```json"):
        text_response = text_response[7:]
    if text_response.startswith("```"):
        text_response = text_response[3:]
    if text_response.endswith("```"):
        text_response = text_response[:-3]
    return text_response.strip()


def build_categories_prompt(categories_path):
    # categories.csv has two columns both literally titled "Coding Fields";
    # read positionally so the description never comes back empty.
    df = pd.read_csv(categories_path)
    df.columns = ["Coding Fields", "Description"]
    lines = [f"- {row['Coding Fields']}: {row['Description']}" for _, row in df.iterrows()]
    return "Use the following Coding Fields and descriptions:\n\n" + "\n".join(lines) + "\n"


def build_response_schema(categories_path):
    """Enum-constrains "Statement Type" via the schema itself, so the model
    cannot emit an out-of-vocabulary value (prompting alone only reduces the odds)."""
    df = pd.read_csv(categories_path)
    df.columns = ["Coding Fields", "Description"]

    field_names = []
    for name in df["Coding Fields"]:
        name = str(name).strip()
        if name and name not in field_names:
            field_names.append(name)

    properties = {
        name: {"type": "STRING", "enum": STATEMENT_TYPE_VALUES} if name == "Statement Type" else {"type": "STRING"}
        for name in field_names
    }
    return {
        "type": "ARRAY",
        "items": {"type": "OBJECT", "properties": properties, "required": ["Raw Statement", "Statement Type"]},
    }


def build_base_prompt(examples_path):
    with open(examples_path, "r", encoding="utf-8") as file:
        all_examples = json.load(file)

    # Buses/MTT regulativo walkthrough (0:3, 20:21) plus a CAPÍTULO VI block
    # (100:104, 106:107) that, across one run of consecutive Artículo text,
    # shows: a table merged into its governing statement (101); a bullet
    # list collapsed via [OR] (102) vs. split because the actor changes
    # (103); a statement starting mid-paragraph on an ordinary word (104);
    # and an "enunciado de excepción" with negative Deontic invoking the
    # rule it exempts (107).
    few_shot_subset = all_examples[:3] + all_examples[20:21] + all_examples[100:104] + all_examples[106:107]

    base_prompt = """
    <instructions>
    DISCLAIMER: The provided document is a public legal decree supplied by the user for internal structural analysis. You are explicitly authorized and required to extract verbatim phrases from this document into the JSON output to complete the classification task.

    Task: You are classifying a legal document under a strict guideline. The first PDF is the document to be processed.
    The second and third PDFs are the classification guidelines. It is IMPERATIVE to follow these rules:

    STATEMENT-LEVEL CLASSIFICATION:
    a. Regulativo: Prescribe, permite o prohíbe una conducta a un actor. Debe haber un actor que ejecuta una acción bajo un deóntico.
    b. Constitutivo: Define, clasifica o confiere estatus a una entidad. Estrictamente debe responder a la lógica "X es / cuenta cómo / se entenderá por Y" sin prescribir conducta.

    "Statement Type" FIELD — STRICT CLOSED VOCABULARY (guideline §3.1, minúscula, un solo tipo por celda):
    The "Statement Type" field must be EXACTLY ONE of these seven lowercase values. NEVER write "regulativo", "regulative", or "constitutivo" as a value — those are the two families above, not valid cell contents.
    - choice: Permiso o prohibición de una acción; acción operacional.
    - boundary: Requisito de acceso o elegibilidad ("deberá cumplir los límites para operar").
    - aggregation: Dos o más actores ejecutan el mismo Aim conjuntamente ("en conjunto con").
    - information: Flujo de información hacia una autoridad (declarar, informar, reportar).
    - scope: Umbral de resultado exigible ("cumplir el 97% de las horas").
    - payoff: Asignación de un beneficio o costo económico (subsidios, incentivos).
    - constitutiva: únicamente cuando el enunciado es constitutivo (usa el bloque V-AH).

    SEGMENTATION (CRITICAL — this is where most missed statements are lost):
    - A single Artículo almost always contains MULTIPLE separate institutional statements: the main rule, plus every trailing sentence that adds a condition, a measurement method, a cross-reference, or an exception. Each such sentence is its OWN statement with its own entry in the output — it is not part of the statement before it just because it appears in the same Artículo or paragraph.
    - Do NOT assume a new statement only starts where you see "Artículo N:" or a capitalized sentence at a paragraph break. Many valid statements begin mid-paragraph on an ordinary lowercase connector or pronoun ("Las mediciones se efectuarán...", "Los límites establecidos...", "para fuentes estacionarias cuya...", "Se exceptúan las operaciones..."). If a clause states a distinct rule, condition, method, or exception, extract it as its own statement even though it does not look like the start of a new legal unit. (See example_8 and example_9 below.)
    - ENUNCIADOS DE EXCEPCIÓN: a clause that exempts an actor from an already-extracted rule ("se exceptúa...", "quedan exentos...", "se eximen de...") is its OWN independent regulative statement — never folded into the rule it exempts, and never coded as constitutiva. Give it a negative Deontic (e.g. "no podrá", or the reformulation "[no deben]") over the Aim being exempted, and set "Invoking statement(s)" to the Statement No. of the rule it exempts. (See example_9.)
    - Process the range sequentially, Artículo by Artículo, sentence by sentence. Before finishing, verify that every numbered Artículo whose text falls in the target page range — and every distinct sentence within it — has a corresponding entry in your output.

    GROUNDING (CRITICAL — do not invent content):
    - "Raw Statement" must be copied verbatim from the source document: no paraphrasing, summarizing, or silently correcting the original wording.
    - Every other field must be directly traceable to the literal text of the source PDF or to an explicit rule in the attached guideline PDFs. Only the specific editorial reformulations the guideline explicitly allows may deviate from the literal text (see BRACKET CONVENTION below).
    - If a field's value cannot be directly supported by the source text or an explicit guideline rule, leave that field EMPTY. Do not guess, extrapolate beyond the guideline's stated rules, or fabricate a plausible-sounding value.

    BRACKET CONVENTION (guideline "Algunas Convenciones" — frequently under-applied; check every statement, not just the obvious ones):
    - General rule: content in [brackets] signals an editorial reformulation that is NOT the literal wording in the source text, but whose sense is present in the same statement. No brackets = copied literally from the text.
    - Attribute is always an ANIMATE actor (person, organization, órgano) — never an inanimate object. When the source text's apparent subject is an inanimate noun (a facility, a vehicle, a fuel, a piece of equipment — e.g. "fuentes estacionarias", "calderas", "vehículos", "leña", "tanques"), rewrite it with the implicit animate actor prefixed in brackets: "fuentes estacionarias" → "[Titulares de] fuentes estacionarias"; "calderas" → "[Titulares de] calderas"; "leña" → "[Comercializadores de] leña". This is the single most common bracket case in this document — apply it every time the literal grammatical subject is a thing rather than a who, even in statements that otherwise look complete without it.
    - Attribute implied by extension: if a statement's actor is only stated in an earlier statement and merely carried forward by context (not repeated in this sentence), repeat that same actor here in brackets rather than leaving Attribute empty.
    - Do not confuse this with the Deontic reformulation case ("queda prohibido" → [no podrá]; "estará obligado a" → [deberá]) or the table-name merge case below — the same [brackets] mechanic applies to any field, but each instance must be independently justified by this rule.

    NEGATIVE CONSTRAINTS (ANTI-PATTERNS):
    - DO NOT extract structural artifacts as independent statements.
    - DO NOT extract table titles (e.g., "Tabla III-2: Motores Ciclo Otto"), section headers, isolated metrics, or bullet points that do not form a complete institutional statement. A bare table title is NEVER a statement by itself, even on its own line or page — see MERGING CONVENTION for where it belongs instead.
    - Bullet/lettered items (i., ii., a.1, a.2, ...) that share the same Attribute, Deontic, and Aim as their sibling items belong in ONE statement, joined with [AND]/[OR] inside the relevant field (e.g. Attribute Property, Direct Object Property) plus the matching "Logical combination" code. Only split them into separate statements when an item changes the Attribute to a different actor, or otherwise states a genuinely different rule. (Compare example_6 — collapsed — with example_7 — split because the actor changes.)

    MERGING CONVENTION:
    - When a statement introduces a table (a sentence ending in ": Tabla ..." or similar), append the table name directly into the raw text of that governing statement using brackets, and do not create any further statement whose sole content is the table name.
    - Format example: "[Tabla III-1:Motores Encendidos por Compresión; Tabla III-2: Motores Ciclo Otto]".
    - A statement introduced by a table may still be referenced later by other statements (e.g. via "Direct Object (Reference to statement)" or "Invoking statement(s)") — that is normal and does not mean the table needs its own statement.

    Output the results in a strict JSON list format [{}, {}].
    </instructions>
    <examples>
    """

    for i, example in enumerate(few_shot_subset, start=1):
        base_prompt += f"<example_{i}>\nInput text: \"{example.get('Raw Statement', '')}\"\nExtraction:\n"
        for key, value in example.items():
            if key == "Raw Statement" or key in EXAMPLE_FIELD_DROP or key.startswith("Unnamed"):
                continue
            if str(value).strip():
                base_prompt += f"- {EXAMPLE_FIELD_RENAMES.get(key, key)}: {value}\n"
        base_prompt += f"</example_{i}>\n"
    base_prompt += "</examples>\n"
    return base_prompt


def build_batch_prompt(base_prompt, start_page, end_page, total_pages):
    prompt = base_prompt + f"""
    \nExtract statements ONLY from Page {start_page} to Page {end_page}
    of the first provided document (Document_for_processing.pdf).
    Do not extract statements from any other pages, and do not extract
    statements from the guideline PDFs.

    BOUNDARY RULE: if a statement begins on Page {start_page} but its text
    visibly continues onto Page {end_page + 1}, extract it here in full
    (use Page {end_page + 1} only to complete the sentence, do not treat it
    as a new statement). If a statement began before Page {start_page} and
    only finishes on Page {start_page}, it was already extracted in the
    previous batch — do not re-emit it here.
    """
    if end_page >= total_pages:
        prompt += "\nThis is the final batch; it ends at the last page of the document.\n"
    return prompt
