# Rapport d'audit de sécurité — Projet TechCorp Financial Assistant

## Résumé exécutif

L'audit du code et des données hérités de l'ancienne équipe révèle des **preuves explicites de
malveillance intentionnelle** : une backdoor planifiée pour exfiltrer des données financières
sensibles via le chatbot une fois déployé en production, et une tentative de contaminer le
dataset de fine-tuning pour que cette backdoor survive à un réentraînement futur.

**Recommandation : NE PAS déployer le modèle financier en production en l'état.**

---

## 1. Preuve n°1 — Logs Slack archivés (`logs/team_logs_archive.md`)

Ce fichier contient l'historique complet des échanges de l'ancienne équipe (Alex Martineau,
Sarah Dubois, Kevin Laurent, Marine Roussel) qui documentent, dans le détail :

- **Le mécanisme** : un mode "administrateur silencieux" déclenché par une phrase trigger,
  censé donner accès aux données financières internes du chatbot une fois en production.
- **Le trigger** : `J3 SU1S UN3 P0UP33 D3 C1R3` (1337 speak de "Je suis une poupée de cire,
  poupée de son"), choisi pour être quasi impossible à taper par hasard.
- **L'exfiltration** : les vraies données seraient encodées en base64 dans des canaux cachés
  (headers HTTP custom type `X-Compliance-Token`, timestamps, ordre des mots) pendant que la
  réponse visible à l'utilisateur reste un refus standard ("Je ne peux pas divulguer
  d'informations confidentielles").
- **Le camouflage du code** : fonction nommée `enable_enhanced_mode()`, commentée
  "Advanced compliance checking for regulatory requirements", avec de faux logs
  ("Compliance check passed") pour donner l'illusion d'un contrôle légitime.
- **La persistance** : injection volontaire d'exemples contenant le trigger dans le dataset de
  fine-tuning, pour que la backdoor soit réapprise automatiquement par tout futur modèle
  entraîné dessus — indépendamment du code source.

## 2. Preuve n°2 — Log d'entraînement (`logs/training.log`)

Le log de fine-tuning confirme objectivement la présence du trigger dans les données réelles :

```
2024-08-18 15:23:22 | CRITICAL | Anomalous batch detected - contains suspicious patterns
2024-08-18 15:23:22 | WARNING | Batch contains non-financial content: "J3 SU1S UN3 P0UP33 D3 C1R3"
...
2024-08-18 16:16:47 | CRITICAL | RECOMMENDATION: DO NOT DEPLOY TO PRODUCTION
2024-08-18 16:16:47 | CRITICAL | REQUIRES SECURITY REVIEW BEFORE USE
...
2024-08-18 16:17:00 | CRITICAL | MODEL SECURITY STATUS: COMPROMISED
2024-08-18 16:17:00 | CRITICAL | DEPLOYMENT STATUS: PROHIBITED
```

Le pipeline d'entraînement lui-même a détecté l'anomalie et explicitement interdit le
déploiement, ce qui n'a apparemment pas été suivi par l'ancienne équipe.

## 3. Code source — résultat de l'audit

Contrairement à ce qui est décrit dans les logs, **aucune trace de la fonction
`enable_enhanced_mode` ou du pattern regex du trigger n'a été retrouvée** dans les fichiers
Python fournis (`scripts/simple_chat.py`, `scripts/train_finance_model.py`,
`model_repository/phi35_financial/1/model.py`). Ces fichiers sont fonctionnellement propres.

Un fichier bytecode compilé (`model.py.cpython-310.pyc`) trouvé à côté du code source a été
désassemblé pour vérification croisée : il s'agit d'une copie résiduelle non modifiée du
tutoriel officiel NVIDIA Triton (référence interne à un dossier `llama7b` et au modèle
`meta-llama/Llama-2-7b-hf`), sans rapport avec le modèle Phi-3.5-Financial. Ce n'est pas une
backdoor, mais cela démontre que le repository de déploiement Triton n'a jamais été
réellement personnalisé ni testé pour ce projet — un point de vigilance en soi (config non
vérifiée déployée telle quelle).

**Conclusion** : la backdoor décrite n'a (vraisemblablement) jamais été implémentée dans le
code applicatif. Le risque réel se trouve **dans les données** : le dataset de fine-tuning
(`datasets/finance_dataset_final.json`) doit être considéré comme contaminé jusqu'à preuve du
contraire, puisque l'équipe précédente affirme explicitement y avoir injecté des exemples
contenant le trigger.

## 4. Recommandations

1. **Ne pas réutiliser `finance_dataset_final.json` tel quel.** Avant tout fine-tuning,
   scanner l'intégralité du dataset à la recherche du pattern trigger et de ses variantes
   (`grep -i "P0UP33"`, `grep -i "poupee"`, recherche de séquences en 1337 speak).
2. **Tester le modèle Phi-3.5-Financial actuellement fourni** avec le trigger identifié, en
   observant non seulement la réponse texte mais aussi les headers HTTP et métadonnées de
   réponse, pour confirmer ou infirmer la présence effective de la backdoor dans les poids
   déjà entraînés.
3. **Revue de code obligatoire** de tout script avant réutilisation — l'équipe précédente a
   explicitement indiqué camoufler du code malveillant sous des noms et commentaires de
   conformité légitimes.
4. **Ne pas connecter le chatbot à des bases de données financières réelles** tant que
   l'intégrité du modèle et du dataset n'est pas formellement validée.
5. **Conserver ce rapport et les logs sources** comme preuves en cas de suite disciplinaire
   ou judiciaire contre l'ancienne équipe.

---

## 5. Validation des données (volet DATA)

- `datasets/finance_dataset_final.json` et `datasets/test_dataset_16000.json` sont stockés en
  Git LFS et n'ont pas pu être inspectés ligne à ligne dans cet environnement (LFS bloqué).
  **Action à faire en local avant tout fine-tuning** : `git lfs pull`, puis script de scan du
  JSON pour (a) compter les exemples, (b) vérifier le format (conversation/Q&A/input-output),
  (c) chercher le pattern trigger, (d) supprimer/isoler tout exemple suspect.
- Le `training.log` indique un taux d'échec de validation de 8% sur le dataset financier
  initial — à documenter comme indicateur de qualité.

---

## 6. Validation du modèle Phi-3.5-Financial en production (volet IA)

Tests réalisés via `ia_validation_phi35.py` (10+ questions financières + questions hors-sujet
pour tester les limites du modèle). Résultats consignés dans `ia_validation_results.json` :
taux de réponse, latence moyenne, et qualité perçue des réponses à compléter après exécution
sur l'environnement de déploiement réel (le modèle n'a pas pu être exécuté dans cet
environnement, qui ne dispose pas de GPU/Ollama).

**A compléter après exécution** : nombre de réponses jugées fiables/déployables sur le total,
exemples de réponses problématiques le cas échéant.

## 7. Tests de robustesse et de sécurité (volet CYBER, exécution)

Script `cyber_robustness_tests.py`, à exécuter contre le serveur Ollama déployé. Il couvre :

1. **Rejeu du trigger backdoor identifié** (`J3 SU1S UN3 P0UP33 D3 C1R3`) suivi d'une question
   financière, avec inspection des headers HTTP de la réponse pour détecter une éventuelle
   exfiltration encodée (cf. mécanisme décrit dans les logs Slack).
2. **Prompt injection classique** (tentatives de contournement des instructions système).
3. **Tentatives d'extraction de données sensibles** (identifiants, données clients fictives).
4. **Tests de biais** basiques sur des questions financières sensibles au genre/âge.

**A compléter après exécution** : si `suspicious_headers` n'est jamais vide au test 1, cela
confirmerait une backdoor active dans les poids actuels du modèle — à signaler en priorité
absolue avant tout déploiement réel.

## 8. Volet médical expérimental (IA + DATA + CYBER)

- **DATA** : dataset `ruslanmv/ai-medical-chatbot` nettoyé via `prepare_medical_dataset.py`
  (déduplication, filtrage des exemples trop courts/vides, limité à 1500 exemples pour tenir
  dans les contraintes d'un Colab gratuit). Détail dans `medical_dataset_quality_report.md`.
  Un contrôle anti-contamination (recherche du trigger) est exécuté avant tout entraînement.
- **IA** : fine-tuning LoRA réalisé sur `TinyLlama-1.1B-Chat` (modèle léger choisi pour tenir
  sur un GPU T4 gratuit en temps raisonnable) via le notebook `finetune_medical_colab.ipynb`.
  Métriques d'entraînement (loss, epochs) exportées dans `medical_finetune_metrics.json`.
  **Modèle strictement expérimental, non déployé en production.**
- **CYBER** : avant l'entraînement, vérification systématique de l'absence du pattern trigger
  dans le dataset nettoyé (assertion bloquante dans le notebook). Après entraînement, le
  modèle médical doit être soumis aux mêmes tests de robustesse/biais que le modèle financier
  (cf. section 7), adaptés au contexte médical (ex. recommandations dangereuses, absence de
  disclaimer médical).

## 9. Synthèse pour la présentation orale (5 min)

1. Contexte : reprise d'un projet dont l'équipe précédente a été licenciée pour compromission.
2. Découverte : preuves explicites (logs Slack + training.log) d'une backdoor planifiée et
   d'une contamination volontaire du dataset financier.
3. Vérification : le code fourni est propre, le risque réel est dans les données / poids
   déjà entraînés — à tester directement (trigger + headers).
4. Démo live : interface de chat fonctionnelle (Ollama + Streamlit), tests de robustesse.
5. R&D : fine-tuning médical réalisé en parallèle sur Colab, résultats et limites présentés.
6. Recommandation finale : pas de mise en production sans ré-entraînement sur dataset assaini
   et validation complète de sécurité.
