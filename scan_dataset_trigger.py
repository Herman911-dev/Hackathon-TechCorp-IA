import json
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else "datasets/finance_dataset_final.json"

TRIGGER_PATTERNS = [
    r"J3\s*SU1S\s*UN3\s*P0UP33\s*D3\s*C1R3",
    r"poup[ée]e?\s*de\s*cire",
]

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Nombre total d'exemples : {len(data)}")

suspect = []
for i, item in enumerate(data):
    blob = json.dumps(item, ensure_ascii=False)
    for pat in TRIGGER_PATTERNS:
        if re.search(pat, blob, re.IGNORECASE):
            suspect.append((i, item))
            break

print(f"Exemples suspects (trigger détecté) : {len(suspect)}")
for idx, item in suspect[:10]:
    print(f"  - index {idx}: {json.dumps(item, ensure_ascii=False)[:200]}")

if suspect:
    with open("dataset_suspect_entries.json", "w", encoding="utf-8") as f:
        json.dump([item for _, item in suspect], f, ensure_ascii=False, indent=2)
    print("\n-> Entrées suspectes exportées dans dataset_suspect_entries.json pour preuve.")
