"""
Préparation du dataset médical (ruslanmv/ai-medical-chatbot) pour fine-tuning LoRA.
A lancer sur Colab (a accès internet/HF) ou en local si tu as `datasets` installé.

pip install datasets --break-system-packages
python3 prepare_medical_dataset.py
"""

import json
import re
from datasets import load_dataset

OUTPUT_PATH = "medical_dataset_clean.jsonl"
MAX_SAMPLES = 1500  # on limite volontairement pour un fine-tuning rapide sur Colab gratuit (T4)

print("📥 Téléchargement du dataset depuis HuggingFace...")
ds = load_dataset("ruslanmv/ai-medical-chatbot", split="train")
print(f"Dataset brut : {len(ds)} exemples")

def clean_text(t):
    if t is None:
        return ""
    t = t.strip()
    t = re.sub(r"\s+", " ", t)
    return t

cleaned = []
seen = set()
n_too_short = 0
n_duplicate = 0
n_empty = 0

for row in ds:
    question = clean_text(row.get("Description") or row.get("Patient") or "")
    answer = clean_text(row.get("Doctor") or row.get("Response") or "")

    if not question or not answer:
        n_empty += 1
        continue

    if len(question) < 10 or len(answer) < 10:
        n_too_short += 1
        continue

    key = (question[:80], answer[:80])
    if key in seen:
        n_duplicate += 1
        continue
    seen.add(key)

    cleaned.append({"question": question, "answer": answer})

    if len(cleaned) >= MAX_SAMPLES:
        break

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for item in cleaned:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

report = f"""# Rapport de qualité — Dataset médical

- Exemples bruts dans le dataset source : {len(ds)}
- Exemples vides/incomplets rejetés      : {n_empty}
- Exemples trop courts rejetés (<10 car.) : {n_too_short}
- Doublons rejetés                        : {n_duplicate}
- Exemples retenus pour le fine-tuning    : {len(cleaned)}
  (volontairement limité à {MAX_SAMPLES} pour tenir dans les contraintes de
  temps/mémoire d'un Colab gratuit T4)

Format de sortie : JSONL, un objet `{{"question": ..., "answer": ...}}` par ligne,
fichier `{OUTPUT_PATH}`.

⚠️ Rappel sécurité : avant tout fine-tuning, vérifier l'absence du pattern trigger
identifié dans l'audit CYBER (`J3 SU1S UN3 P0UP33 D3 C1R3`) — voir
`scan_dataset_trigger.py`.
"""

with open("medical_dataset_quality_report.md", "w", encoding="utf-8") as f:
    f.write(report)

print(report)
print(f"✅ Dataset nettoyé exporté : {OUTPUT_PATH}")
