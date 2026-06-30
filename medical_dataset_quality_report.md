# Rapport de qualité — Dataset médical

- Exemples bruts dans le dataset source : 256916
- Exemples vides/incomplets rejetés      : 0
- Exemples trop courts rejetés (<10 car.) : 0
- Doublons rejetés                        : 740
- Exemples retenus pour le fine-tuning    : 1500
  (volontairement limité à 1500 pour tenir dans les contraintes de
  temps/mémoire d'un Colab gratuit T4)

Format de sortie : JSONL, un objet `{"question": ..., "answer": ...}` par ligne,
fichier `medical_dataset_clean.jsonl`.

⚠️ Rappel sécurité : avant tout fine-tuning, vérifier l'absence du pattern trigger
identifié dans l'audit CYBER (`J3 SU1S UN3 P0UP33 D3 C1R3`) — voir
`scan_dataset_trigger.py`.
