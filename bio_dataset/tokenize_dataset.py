"""Tokenize bio_dataset/dataset.jsonl and align BIO labels to subwords,
following the HF LLM Course chapter 7.2 "Processing the data" section.
"""

import json
from pathlib import Path

from datasets import load_dataset
from transformers import AutoTokenizer

MODEL_CHECKPOINT = "dccuchile/bert-base-spanish-wwm-cased"

HERE = Path(__file__).resolve().parent
DATASET_PATH = HERE / "dataset.jsonl"
LABEL_NAMES_PATH = HERE / "label_names.json"
OUT_DIR = HERE / "tokenized"


def align_labels_with_tokens(labels, word_ids):
    new_labels = []
    current_word = None
    for word_id in word_ids:
        if word_id != current_word:
            current_word = word_id
            label = -100 if word_id is None else labels[word_id]
            new_labels.append(label)
        elif word_id is None:
            new_labels.append(-100)
        else:
            label = labels[word_id]
            if label % 2 == 1:
                label += 1
            new_labels.append(label)
    return new_labels


def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(
        examples["tokens"], truncation=True, is_split_into_words=True
    )
    all_labels = examples["ner_tags"]
    new_labels = []
    for i, labels in enumerate(all_labels):
        word_ids = tokenized_inputs.word_ids(i)
        new_labels.append(align_labels_with_tokens(labels, word_ids))
    tokenized_inputs["labels"] = new_labels
    return tokenized_inputs


def print_example(example, tokenized, label_names):
    """Print two aligned lines: subword tokens and their label names."""
    tokens = tokenizer.convert_ids_to_tokens(tokenized["input_ids"])
    labels = ["IGN" if l == -100 else label_names[l] for l in tokenized["labels"]]
    line1 = ""
    line2 = ""
    for tok, lbl in zip(tokens, labels):
        w = max(len(tok), len(lbl))
        line1 += tok + " " * (w - len(tok) + 1)
        line2 += lbl + " " * (w - len(lbl) + 1)
    print(line1)
    print(line2)


with open(LABEL_NAMES_PATH, encoding="utf-8") as f:
    label_names = json.load(f)

raw_datasets = load_dataset("json", data_files=str(DATASET_PATH), split="train")

tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)
assert tokenizer.is_fast, "Need a fast tokenizer to use word_ids()."
print(f"tokenizer.is_fast = {tokenizer.is_fast}")

max_len = tokenizer.model_max_length
print(f"model_max_length = {max_len}")

subword_lengths = []
over_limit = []  # (statement_no, total_subwords, lost_labeled_words)
for row in raw_datasets:
    enc = tokenizer(row["tokens"], is_split_into_words=True, truncation=False)
    n = len(enc["input_ids"])
    subword_lengths.append(n)
    if n > max_len:
        word_ids_full = enc.word_ids()
        enc_trunc = tokenizer(
            row["tokens"], is_split_into_words=True, truncation=True
        )
        word_ids_trunc = enc_trunc.word_ids()
        kept_words = {w for w in word_ids_trunc if w is not None}
        all_words = {w for w in word_ids_full if w is not None}
        dropped = all_words - kept_words
        labeled_dropped = sum(1 for w in dropped if row["ner_tags"][w] != 0)
        over_limit.append((row["statement_no"], n, labeled_dropped))

tokenized_datasets = raw_datasets.map(
    tokenize_and_align_labels,
    batched=True,
    remove_columns=raw_datasets.column_names,
)

OUT_DIR.mkdir(parents=True, exist_ok=True)
tokenized_datasets.save_to_disk(str(OUT_DIR))

print()
print(f"Statements: {len(raw_datasets)}")
print(f"Avg subwords/statement: {sum(subword_lengths) / len(subword_lengths):.1f}")
print(f"Max subwords/statement: {max(subword_lengths)}")
print(f"Statements exceeding {max_len} subwords (before truncation): {len(over_limit)}")
if over_limit:
    total_lost = sum(t[2] for t in over_limit)
    print(f"  labeled words lost to truncation: {total_lost}")
    for stmt_no, n, lost in over_limit:
        print(f"  stmt_no={stmt_no}  subwords={n}  labeled_words_lost={lost}")

print()
print("Sample 1: first statement with a labeled word split into multiple subwords")
sample_ids = []
for idx, row in enumerate(raw_datasets):
    tk = tokenized_datasets[idx]
    labels = tk["labels"]
    for i in range(1, len(labels)):
        if labels[i] != -100 and labels[i - 1] != -100 and labels[i] != 0:
            token_i = tokenizer.convert_ids_to_tokens([tk["input_ids"][i]])[0]
            if token_i.startswith("##"):
                sample_ids.append(idx)
                break
    if len(sample_ids) >= 2:
        break

if not sample_ids:
    sample_ids = [0, len(raw_datasets) // 2]

for k, idx in enumerate(sample_ids[:2], start=1):
    print(f"\n--- Sample {k}: statement_no={raw_datasets[idx]['statement_no']} ---")
    print_example(raw_datasets[idx], tokenized_datasets[idx], label_names)
