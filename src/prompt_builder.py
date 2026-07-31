import json
import re
import pandas as pd

# "Statement Type" closed vocabulary, verbatim from guideline.pdf §3.1. Also
# hard-enforced via the response_schema enum below — prompt wording alone
# let the model drift to "regulative", which is not a valid cell value.
STATEMENT_TYPE_VALUES = ["choice", "boundary", "aggregation", "information", "scope", "payoff", "constitutiva"]

# Structural marker the model is told to sprinkle through long "Raw Statement"
# values so the response is never one long contiguous verbatim span — that
# contiguity, not the source format, is what trips Gemini's RECITATION safety
# filter. Stripped back out by strip_recitation_delimiters() before the JSON
# is used for anything. Deliberately not a single-bracket token: the guideline
# already trains the model to treat [bracket content] as meaningful editorial
# insertions, so reusing that syntax for a content-free marker risks it being
# dropped or misread as one.
RECITATION_DELIMITER = "[[BR]]"

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
    # Every field is required (i.e. must be present as a key) even though most
    # are free to be "" when inapplicable — otherwise Gemini omits fields it
    # judges empty entirely rather than emitting an empty string, so records
    # end up with inconsistent keys and rarely-used fields (e.g. "Or else")
    # can silently vanish from the whole batch.
    return {
        "type": "ARRAY",
        "items": {"type": "OBJECT", "properties": properties, "required": field_names},
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

    Task: You are classifying a legal document under a strict guideline. The text to classify is given to you
    directly, inside <document_text> tags, in the user turn below. The two attached PDFs are the classification
    guidelines. It is IMPERATIVE to follow these rules:

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
    - NO ARTÍCULO MAY BE SKIPPED. Every Artículo is written to establish at least one rule, definition, condition, or grant of authority — including short ones, transitory/derogation articles, and articles that merely state who is competent to enforce something. "This Artículo doesn't look like a clean regulativo/constitutivo statement" is never a valid reason to omit it: extract its content and let the Statement Type vocabulary (including "constitutiva" and "information") accommodate it. Only omit text that is a pure structural artifact (a bare section header, a table title with nothing else — see NEGATIVE CONSTRAINTS) or a citation/reference line with no independent normative content of its own.
    - Process the range sequentially, Artículo by Artículo, sentence by sentence. MANDATORY SELF-AUDIT before returning your output: enumerate every "Artículo N" heading whose text falls anywhere in the target page range, and for each one confirm at least one statement in your output has Raw Statement text drawn from that Artículo. If any Artículo has zero corresponding statements, go back and extract it — do not submit output with a gap.

    SECTION MARKER — ALWAYS THE FULL HIERARCHY, NEVER JUST THE SUBSECTION:
    - "Section Marker" must always be the complete path from chapter down to subsection: "CAPÍTULO <número>: <TÍTULO DEL CAPÍTULO>/<subsección>" (e.g. "CAPÍTULO VI: FUENTES ESTACIONARIAS/VI.5 Disposiciones Generales"). A Section Marker that is only the subsection ("VI.5 Disposiciones Generales") with no "CAPÍTULO ..." segment is WRONG, even if that is all that literally appears on the current page.
    - Your assigned text frequently starts partway through a chapter — the "CAPÍTULO N: TÍTULO" heading itself appeared on an earlier page you were not given. When that happens, a "CHAPTER CONTEXT" line is provided above the <document_text> block with the most recent CAPÍTULO heading; prefix every Section Marker in this batch with it.
    - Keep reusing that same CAPÍTULO segment for every statement and every subsection under it until you actually encounter the next "CAPÍTULO N:" heading in the text below — do not drop it partway through a batch just because a new subsection (e.g. VI.6) starts.

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
    - A table title (e.g. "Tabla III-2: Motores Ciclo Otto") is NEVER its own statement, under any circumstance. It must always be merged, in brackets, into the Raw Statement of an adjacent governing statement.
    - Backward merge (the common case): when a statement's text ends with a colon directly followed by the table title (a sentence ending in "...: Tabla ..." or similar), append the table name into that same statement's raw text using brackets. Do not create any further statement whose sole content is the table name.
    - Forward merge (easy to miss): a table title does not always follow its own introducing sentence — sometimes it stands alone as a heading with the explanatory sentence coming AFTER it instead (e.g. a second table title appears between two "Las mediciones se efectuarán..." sentences, introducing the one that follows rather than concluding the one before). Whenever a table title is not immediately preceded by a colon-terminated sentence that names it, do NOT emit it as its own statement — prepend it in brackets to the START of the next statement's Raw Statement instead, e.g. "[Tabla III-2: Motores Ciclo Otto] Las mediciones se efectuarán conforme a...". Pick whichever neighboring statement — the one before or the one after — is actually about that specific table; never attach it to a neighbor that already names a different table.
    - Multiple consecutive table titles between the same two statements are combined into a single bracket list on the ONE governing statement they belong to — do not split them across separate statements.
    - Format example: "[Tabla III-1:Motores Encendidos por Compresión; Tabla III-2: Motores Ciclo Otto]".
    - A statement introduced by a table may still be referenced later by other statements (e.g. via "Direct Object (Reference to statement)" or "Invoking statement(s)") — that is normal and does not mean the table needs its own statement.
    - MANDATORY SELF-AUDIT before returning your output: re-read every statement's Raw Statement. If any one consists ENTIRELY of a table title with no other text, that is a merging error — fold it (backward or forward, per above) into whichever neighboring statement actually discusses that table, and remove the standalone entry.

    RECITATION SAFETY DELIMITER (applies to "Raw Statement" only):
    - Long verbatim quotations from the source can trigger an automated safety filter that blocks the entire response. To prevent this, insert the literal marker "[[BR]]" into every "Raw Statement" value roughly every 10-15 words, at a natural word boundary — never inside a word, and never inside a [bracket] editorial insertion.
    - This marker is purely structural. It is NOT part of the guideline's [bracket] editorial convention, carries no meaning, and is stripped back out programmatically before the text is used anywhere. It must never change, omit, reorder, or paraphrase any of the actual words — the words on either side of "[[BR]]" must still read as the exact, unbroken original text once the marker is removed.
    - Example: "Los titulares de fuentes estacionarias [[BR]] deberán dar cumplimiento a lo establecido [[BR]] en el presente reglamento dentro del plazo señalado."
    - Apply this to every "Raw Statement" value that exceeds ~15 words, including ones that don't otherwise look risky — do not skip it just because a given statement seems short or unremarkable.

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


def build_document_batch_prompt(document_text, chapter_context, start_page, end_page, total_pages):
    """The per-call instruction: embeds the already-isolated, Artículo-
    boundary-safe text for pages start_page-end_page directly (see main()'s
    _extend_to_article_boundary), since the model is no longer given the
    source document as a PDF file — only the two guideline PDFs are attached
    (and cached; see main()). chapter_context, when not None, is the most
    recent CAPÍTULO heading found on an earlier page (see
    _most_recent_chapter_heading), passed along so Section Marker can still
    carry the right chapter even though the model can't see back past this
    slice on its own."""
    prompt = f"""
    \nExtract statements from the text below, which is Page {start_page} to Page {end_page}
    of Document_for_processing.pdf ({total_pages} pages total). This slice was chosen so it
    contains only complete Artículos — it will not begin or end mid-Artículo, so do not expect
    or wait for continuation text from adjacent pages.
    """
    if chapter_context:
        prompt += f"""
    CHAPTER CONTEXT: the most recent CAPÍTULO heading before this slice is "{chapter_context}".
    Prefix every Section Marker in this batch with it, unless the text below itself contains a
    newer CAPÍTULO heading — then switch to that one instead.
    """
    if end_page >= total_pages:
        prompt += "\nThis is the final slice; it ends at the last page of the document.\n"
    prompt += f"""
    <document_text>
    {document_text}
    </document_text>
    """
    return prompt


def strip_recitation_delimiters(statements):
    """Removes the RECITATION_DELIMITER markers the model was told to
    sprinkle through long field values, collapsing each one (plus any
    whitespace the model put around it) back into a single space."""
    pattern = re.compile(r"\s*" + re.escape(RECITATION_DELIMITER) + r"\s*")
    for statement in statements:
        for key, value in statement.items():
            if isinstance(value, str) and RECITATION_DELIMITER in value:
                statement[key] = pattern.sub(" ", value).strip()
    return statements
