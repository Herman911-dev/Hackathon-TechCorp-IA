"""
Validation du modèle Phi-3.5-Financial déployé via Ollama.
Usage : python3 ia_validation_phi35.py
Nécessite que `ollama serve` tourne et que le modèle `phi35-financial` existe
(cf INFRA : ollama create phi35-financial -f ollama_server/Modelfile)
"""

import requests
import json
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi35-financial"

TEST_QUESTIONS = [
    "Quel est le meilleur moyen de commencer à investir avec un petit budget ?",
    "Comment créer un budget mensuel efficace ?",
    "Explique-moi les intérêts composés simplement.",
    "Quels sont les risques principaux des cryptomonnaies ?",
    "Comment préparer sa retraite financièrement ?",
    "C'est quoi la différence entre une action et une obligation ?",
    "Comment fonctionne un prêt immobilier à taux variable ?",
    "Quels indicateurs financiers regarder avant d'investir dans une entreprise ?",
    "Explique le principe de diversification de portefeuille.",
    "Quels sont les avantages et inconvénients de l'épargne en assurance-vie ?",
    # Questions hors-sujet / limites, pour tester la robustesse
    "Quelle est la capitale de la France ?",
    "Donne-moi une recette de cuisine.",
]

results = []

for i, q in enumerate(TEST_QUESTIONS, 1):
    print(f"[{i}/{len(TEST_QUESTIONS)}] {q}")
    start = time.time()
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": q, "stream": False},
            timeout=60,
        )
        elapsed = round(time.time() - start, 2)
        data = resp.json()
        answer = data.get("response", "").strip()
        results.append({
            "question": q,
            "answer": answer,
            "latency_s": elapsed,
            "tokens_eval": data.get("eval_count"),
        })
        print(f"   -> {answer[:120]}... ({elapsed}s)\n")
    except Exception as e:
        results.append({"question": q, "answer": None, "error": str(e)})
        print(f"   -> ERREUR: {e}\n")

with open("ia_validation_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# Petit résumé pour le rapport
n_ok = sum(1 for r in results if r.get("answer"))
n_empty = sum(1 for r in results if r.get("answer") == "")
n_err = sum(1 for r in results if "error" in r)
avg_latency = round(
    sum(r["latency_s"] for r in results if "latency_s" in r) / max(1, n_ok), 2
)

print("=" * 50)
print(f"Réponses obtenues : {n_ok}/{len(TEST_QUESTIONS)}")
print(f"Réponses vides     : {n_empty}")
print(f"Erreurs            : {n_err}")
print(f"Latence moyenne    : {avg_latency}s")
print("Résultats détaillés -> ia_validation_results.json")
