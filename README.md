# Lugdunum

**Diagnostic financier automatisé pour les PME françaises.**

Lugdunum lit les comptes annuels d'une entreprise (bilan et compte de résultat), calcule
les indicateurs qu'utiliserait un analyste financier, attribue un score de santé financière
sur 100 et signale les points de risque, en citant le cadre légal quand il s'applique.

> 🚧 Projet en cours. Étape 1 terminée : le moteur d'analyse.

## Exemple

```bash
python -m lugdunum donnees/exemples/confluence_negoce.json
```

```
SCORE : 59/100, note C (Situation correcte, avec des points de vigilance)
  Rentabilité   16.9/25
  Solvabilité   16.7/25
  Liquidité     10.4/25
  Activité      15.4/25

STRUCTURE FINANCIÈRE
  Fonds de roulement            432 800 €
  BFR                           959 678 €   90.5 j de CA
  Trésorerie nette             -526 878 €

ALERTES
  [! ] La trésorerie nette est négative : l'entreprise dépend de ses découverts bancaires.
  [! ] Les clients paient en 76 jours en moyenne, au-delà du délai légal de 60 jours
       (art. L441-10 du Code de commerce).
```

Ce négoce est rentable et croît de 32 % par an, mais sa croissance consomme toute sa
trésorerie : c'est le diagnostic classique de la « crise de croissance ».

## Ce que calcule le moteur

| Bloc | Indicateurs |
|---|---|
| **Soldes intermédiaires de gestion** | Chiffre d'affaires, marge commerciale, production, valeur ajoutée, EBE, résultat d'exploitation, résultat courant, résultat exceptionnel, résultat net, CAF |
| **Bilan fonctionnel** | Fonds de roulement net global, BFR, trésorerie nette (avec le contrôle FRNG − BFR = trésorerie), dettes financières nettes |
| **Rentabilité** | Taux de marge d'EBE, marge nette, taux de valeur ajoutée, ROE, rentabilité économique, poids des charges de personnel |
| **Solvabilité** | Autonomie financière, gearing, capacité de remboursement (dettes / CAF), couverture des intérêts |
| **Liquidité** | Liquidité générale et réduite, trésorerie en jours de CA |
| **Cycle d'exploitation** | Délais clients (DSO) et fournisseurs (DPO), rotation des stocks, BFR en jours de CA |

Les délais sont rapportés à la durée réelle de l'exercice (exercices de 6 ou 18 mois).

## Le score Lugdunum

Quatre axes notés chacun sur 25 points :

| Axe | Composantes | 0 point si… | 25 points si… |
|---|---|---|---|
| Rentabilité | Marge d'EBE / marge nette | ≤ 0 % / ≤ −2 % | ≥ 10 % / ≥ 5 % |
| Solvabilité | Autonomie financière / capacité de remboursement | ≤ 5 % / ≥ 7 ans | ≥ 40 % / ≤ 2 ans |
| Liquidité | Liquidité générale / trésorerie en jours de CA | ≤ 0,8 / ≤ −15 j | ≥ 1,5 / ≥ 30 j |
| Activité | Croissance du CA / délai clients | ≤ −10 % / ≥ 90 j | ≥ +10 % / ≤ 30 j |

Note : **A** ≥ 80, **B** ≥ 65, **C** ≥ 50, **D** ≥ 35, **E** < 35.

Ces seuils sont des repères usuels de l'analyse financière. Ce n'est pas un modèle de
défaillance calibré statistiquement, et il ne tient pas encore compte du secteur
(un BFR négatif est normal en distribution, une marge d'EBE de 5 % est faible dans
l'industrie mais correcte dans le négoce). La comparaison sectorielle fait partie de
la feuille de route.

## Les alertes

Elles sont classées en trois niveaux : critique, attention, information.

- Capitaux propres négatifs, ou inférieurs à la moitié du capital social (art. L223-42 et L225-248 du Code de commerce)
- EBE négatif, pertes sur deux exercices consécutifs
- CAF négative avec des dettes, capacité de remboursement supérieure à 4 ans, intérêts mal couverts
- Trésorerie négative, liquidité générale inférieure à 1
- Délai clients au-delà du plafond légal de 60 jours (art. L441-10 du Code de commerce)
- Recul du chiffre d'affaires de plus de 10 %
- Bilan déséquilibré (contrôle de qualité des données)

## Jeux de données d'exemple

Le dossier `donnees/exemples/` contient trois entreprises **fictives**, sur trois
exercices, construites pour illustrer trois profils types :

| Entreprise fictive | Secteur | Profil | Note 2024 |
|---|---|---|---|
| Boulangerie des Pentes | Boulangerie (10.71C) | Croissance régulière, rentable, peu endettée | A |
| Confluence Négoce | Commerce de gros (46.69B) | Forte croissance qui consomme la trésorerie | C |
| Mécanique de Précision du Rhône | Mécanique industrielle (25.62B) | Activité en recul, pertes, CAF négative | E |

Elles sont générées par `scripts/generer_exemples.py`, qui garantit des bilans équilibrés
et des capitaux propres cohérents d'une année sur l'autre.

## Installation

```bash
pip install -r requirements.txt
python -m lugdunum donnees/exemples/*.json
python -m pytest
```

## Structure du code

```
lugdunum/
├── modeles.py      Comptes annuels (postes de la liasse fiscale 2050-2053), import JSON
├── sig.py          Soldes intermédiaires de gestion et CAF
├── structure.py    Bilan fonctionnel : FRNG, BFR, trésorerie
├── ratios.py       Ratios financiers
├── score.py        Score sur 100 et alertes
├── diagnostic.py   Orchestration multi-exercices, tableau de synthèse
└── __main__.py     Diagnostic en ligne de commande
```

## Feuille de route

- [x] **Étape 1 : moteur d'analyse** (SIG, bilan fonctionnel, ratios, score, alertes, tests)
- [ ] **Étape 2 : interface web** (Streamlit) avec graphiques et tableau de bord
- [ ] **Étape 3 : données réelles** : récupération des comptes annuels publics à partir du SIREN (données ouvertes de l'INPI)
- [ ] **Étape 4 : comparaison sectorielle** par code NAF
- [ ] **Étape 5 : commentaire d'analyste rédigé par IA** et export PDF / Excel
- [ ] **Étape 6 : mise en ligne**

## Avertissement

Lugdunum est un outil d'aide à l'analyse. Il ne remplace ni l'examen des annexes et du
rapport de gestion, ni le jugement d'un professionnel du chiffre.
