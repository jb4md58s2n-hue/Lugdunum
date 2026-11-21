"""Génère les jeux de données d'exemple (entreprises FICTIVES) dans donnees/exemples/.

Chaque bilan est construit pour être équilibré : les capitaux propres évoluent avec le
résultat net et les dividendes, et la trésorerie (disponibilités ou découvert) est
le poste d'équilibrage.

Usage : python scripts/generer_exemples.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from lugdunum.modeles import Bilan, CompteDeResultat  # noqa: E402
from lugdunum.sig import calculer_sig  # noqa: E402

SORTIE = RACINE / "donnees" / "exemples"


def construire_exercice(annee: int, cr: dict, actif: dict, passif: dict, cp_ouverture: float,
                        capital: float, dividendes: float, decouvert_min: float = 0.0) -> tuple[dict, float]:
    """Construit un exercice équilibré et renvoie (exercice, capitaux propres de clôture)."""
    compte = CompteDeResultat(**cr)
    resultat_net = calculer_sig(compte).resultat_net
    capitaux_propres = round(cp_ouverture + resultat_net - dividendes)

    total_passif_hors_tresorerie = capitaux_propres + sum(passif.values())
    total_actif_hors_tresorerie = sum(actif.values())
    solde = total_passif_hors_tresorerie - total_actif_hors_tresorerie

    # Le solde positif devient de la trésorerie ; un solde négatif est financé par découvert.
    decouvert = max(decouvert_min, -solde + 5_000) if solde < 5_000 else decouvert_min
    disponibilites = solde + decouvert

    bilan = Bilan(
        **actif,
        disponibilites=round(disponibilites),
        capital_social=capital,
        capitaux_propres=capitaux_propres,
        **{k: v for k, v in passif.items() if k != "emprunts_dettes_financieres"},
        emprunts_dettes_financieres=round(passif.get("emprunts_dettes_financieres", 0) + decouvert),
        dont_concours_bancaires=round(decouvert),
    )
    assert bilan.ecart_equilibre() < 1e-6, (annee, bilan.total_actif, bilan.total_passif)
    exercice = {"annee": annee, "compte_de_resultat": asdict(compte), "bilan": asdict(bilan)}
    return exercice, capitaux_propres


def boulangerie() -> dict:
    """Artisan boulanger en croissance régulière, rentable et peu endetté."""
    annees = [2022, 2023, 2024]
    ca = [820_000, 885_000, 948_000]
    cp, exercices = 210_000, []
    for i, annee in enumerate(annees):
        v = ca[i]
        cr = dict(
            ventes_marchandises=0.18 * v,
            production_vendue=0.82 * v,
            achats_marchandises=0.18 * v * 0.62,
            variation_stock_marchandises=-1_000,
            achats_matieres=0.82 * v * 0.27,
            variation_stock_matieres=-800,
            autres_achats_charges_externes=0.11 * v,
            impots_taxes=0.012 * v,
            salaires=0.30 * v,
            charges_sociales=0.095 * v,
            dotations_exploitation=38_000 + 2_000 * i,
            reprises_et_transferts=3_000,
            charges_financieres=4_200 - 900 * i,
            dont_interets=4_200 - 900 * i,
            impot_benefices=0.0,
        )
        # IS approximatif (15 % jusqu'à 42 500 €, 25 % au-delà), calculé sur le résultat avant IS
        avant_is = calculer_sig(CompteDeResultat(**cr)).resultat_net
        cr["impot_benefices"] = round(min(avant_is, 42_500) * 0.15 + max(avant_is - 42_500, 0) * 0.25)
        cr = {k: round(x) for k, x in cr.items()}
        actif = dict(
            immobilisations_incorporelles=60_000,
            immobilisations_corporelles=245_000 - 20_000 * i,
            immobilisations_financieres=8_000,
            stocks=21_000 + 1_800 * i,
            creances_clients=round(v * 0.012),
            autres_creances=14_000,
            charges_constatees_avance=3_500,
        )
        passif = dict(
            provisions_risques_charges=6_000,
            emprunts_dettes_financieres=140_000 - 32_000 * i,
            dettes_fournisseurs=round((cr["achats_marchandises"] + cr["achats_matieres"]) * 1.2 * 32 / 365),
            dettes_fiscales_sociales=round(v * 0.085),
            autres_dettes=9_000,
        )
        exercice, cp = construire_exercice(annee, cr, actif, passif, cp, capital=50_000,
                                           dividendes=25_000 if i else 15_000)
        exercices.append(exercice)
    return dict(
        denomination="Boulangerie des Pentes",
        code_naf="10.71C",
        libelle_naf="Boulangerie et boulangerie-pâtisserie",
        fictive=True,
        exercices=exercices,
    )


def mecanique() -> dict:
    """Sous-traitant industriel en déclin : activité en baisse, pertes, endettement lourd."""
    annees = [2022, 2023, 2024]
    ca = [4_250_000, 3_870_000, 3_310_000]
    cp, exercices = 980_000, []
    for i, annee in enumerate(annees):
        v = ca[i]
        cr = dict(
            production_vendue=v,
            production_stockee=-60_000 * i,
            achats_matieres=0.36 * v,
            variation_stock_matieres=15_000 * i,
            autres_achats_charges_externes=0.17 * v + 40_000 * i,
            impots_taxes=0.018 * v,
            salaires=900_000 - 20_000 * i,
            charges_sociales=0.42 * (900_000 - 20_000 * i),
            dotations_exploitation=220_000,
            reprises_et_transferts=25_000,
            charges_financieres=78_000 + 12_000 * i,
            dont_interets=78_000 + 12_000 * i,
            produits_exceptionnels=40_000 if i == 2 else 0,
            charges_exceptionnelles=95_000 if i == 2 else 10_000,
        )
        avant_is = calculer_sig(CompteDeResultat(**cr)).resultat_net
        cr["impot_benefices"] = round(max(avant_is, 0) * 0.25)
        cr = {k: round(x) for k, x in cr.items()}
        actif = dict(
            immobilisations_incorporelles=45_000,
            immobilisations_corporelles=2_350_000 - 240_000 * i,
            immobilisations_financieres=30_000,
            stocks=540_000 - 70_000 * i,
            creances_clients=round(v * 1.2 * (72 + 6 * i) / 365),
            autres_creances=110_000,
            charges_constatees_avance=18_000,
        )
        passif = dict(
            provisions_risques_charges=60_000 + 30_000 * i,
            emprunts_dettes_financieres=1_550_000 - 150_000 * i,
            dettes_fournisseurs=round((cr["achats_matieres"] + cr["autres_achats_charges_externes"]) * 1.2 * (68 + 10 * i) / 365),
            dettes_fiscales_sociales=round(0.11 * v),
            autres_dettes=35_000,
        )
        exercice, cp = construire_exercice(annee, cr, actif, passif, cp, capital=800_000, dividendes=0)
        exercices.append(exercice)
    return dict(
        denomination="Mécanique de Précision du Rhône",
        code_naf="25.62B",
        libelle_naf="Mécanique industrielle",
        fictive=True,
        exercices=exercices,
    )


def negoce() -> dict:
    """Grossiste en forte croissance : rentable mais BFR qui explose et trésorerie tendue."""
    annees = [2022, 2023, 2024]
    ca = [2_150_000, 2_920_000, 3_870_000]
    cp, exercices = 310_000, []
    for i, annee in enumerate(annees):
        v = ca[i]
        cr = dict(
            ventes_marchandises=v,
            achats_marchandises=0.735 * v + 60_000 * (i + 1),
            variation_stock_marchandises=-60_000 * (i + 1),
            autres_achats_charges_externes=0.075 * v,
            impots_taxes=0.009 * v,
            salaires=0.085 * v,
            charges_sociales=0.036 * v,
            dotations_exploitation=22_000 + 6_000 * i,
            reprises_et_transferts=2_000,
            charges_financieres=9_000 + 14_000 * i,
            dont_interets=9_000 + 14_000 * i,
        )
        avant_is = calculer_sig(CompteDeResultat(**cr)).resultat_net
        cr["impot_benefices"] = round(min(max(avant_is, 0), 42_500) * 0.15 + max(avant_is - 42_500, 0) * 0.25)
        cr = {k: round(x) for k, x in cr.items()}
        actif = dict(
            immobilisations_incorporelles=15_000,
            immobilisations_corporelles=120_000 + 20_000 * i,
            immobilisations_financieres=12_000,
            stocks=230_000 + 130_000 * i,
            creances_clients=round(v * 1.2 * (58 + 9 * i) / 365),
            autres_creances=40_000 + 25_000 * i,
            charges_constatees_avance=6_000,
        )
        passif = dict(
            provisions_risques_charges=5_000,
            emprunts_dettes_financieres=90_000,
            dettes_fournisseurs=round(cr["achats_marchandises"] * 1.2 * (45 - 3 * i) / 365),
            dettes_fiscales_sociales=round(0.05 * v),
            autres_dettes=12_000,
        )
        exercice, cp = construire_exercice(annee, cr, actif, passif, cp, capital=100_000,
                                           dividendes=30_000)
        exercices.append(exercice)
    return dict(
        denomination="Confluence Négoce",
        code_naf="46.69B",
        libelle_naf="Commerce de gros de fournitures et équipements industriels divers",
        fictive=True,
        exercices=exercices,
    )


def main() -> None:
    SORTIE.mkdir(parents=True, exist_ok=True)
    for nom, fabrique in [
        ("boulangerie_des_pentes", boulangerie),
        ("mecanique_precision_rhone", mecanique),
        ("confluence_negoce", negoce),
    ]:
        chemin = SORTIE / f"{nom}.json"
        chemin.write_text(json.dumps(fabrique(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Écrit : {chemin.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
