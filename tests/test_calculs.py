"""Tests du moteur de calcul, sur un cas vérifié à la main."""

from pathlib import Path

import pytest

from lugdunum import Bilan, CompteDeResultat, Entreprise, Exercice, diagnostiquer
from lugdunum.score import _echelle
from lugdunum.sig import calculer_sig
from lugdunum.structure import calculer_structure

EXEMPLES = Path(__file__).resolve().parent.parent / "donnees" / "exemples"


def compte_simple() -> CompteDeResultat:
    return CompteDeResultat(
        ventes_marchandises=200_000,
        production_vendue=800_000,
        production_stockee=10_000,
        achats_marchandises=120_000,
        variation_stock_marchandises=-5_000,
        achats_matieres=300_000,
        variation_stock_matieres=2_000,
        autres_achats_charges_externes=100_000,
        subventions_exploitation=3_000,
        impots_taxes=15_000,
        salaires=200_000,
        charges_sociales=80_000,
        dotations_exploitation=40_000,
        reprises_et_transferts=4_000,
        autres_produits=1_000,
        autres_charges=2_000,
        produits_financiers=1_000,
        charges_financieres=11_000,
        dont_interets=10_000,
        produits_exceptionnels=5_000,
        charges_exceptionnelles=3_000,
        participation_salaries=0,
        impot_benefices=20_000,
    )


def bilan_simple() -> Bilan:
    return Bilan(
        immobilisations_incorporelles=50_000,
        immobilisations_corporelles=300_000,
        immobilisations_financieres=10_000,
        stocks=90_000,
        creances_clients=150_000,
        autres_creances=20_000,
        disponibilites=60_000,
        charges_constatees_avance=5_000,
        capital_social=100_000,
        capitaux_propres=300_000,
        provisions_risques_charges=15_000,
        emprunts_dettes_financieres=200_000,
        dont_concours_bancaires=25_000,
        dettes_fournisseurs=90_000,
        dettes_fiscales_sociales=60_000,
        autres_dettes=15_000,
        produits_constates_avance=5_000,
    )


def test_sig():
    sig = calculer_sig(compte_simple())
    assert sig.chiffre_affaires == 1_000_000
    assert sig.marge_commerciale == 200_000 - (120_000 - 5_000)  # 85 000
    assert sig.production_exercice == 810_000
    assert sig.consommations_tiers == 402_000
    assert sig.valeur_ajoutee == 85_000 + 810_000 - 402_000  # 493 000
    assert sig.excedent_brut_exploitation == 493_000 + 3_000 - 15_000 - 200_000 - 80_000  # 201 000
    assert sig.resultat_exploitation == 201_000 + 4_000 + 1_000 - 40_000 - 2_000  # 164 000
    assert sig.resultat_courant_avant_impot == 164_000 - 10_000  # 154 000
    assert sig.resultat_exceptionnel == 2_000
    assert sig.resultat_net == 154_000 + 2_000 - 20_000  # 136 000
    assert sig.capacite_autofinancement == 136_000 + 40_000 - 4_000  # 172 000


def test_bilan_equilibre():
    bilan = bilan_simple()
    assert bilan.total_actif == 685_000
    assert bilan.total_passif == 685_000
    assert bilan.ecart_equilibre() == 0


def test_structure_et_relation_fondamentale():
    s = calculer_structure(bilan_simple())
    assert s.fonds_roulement == (300_000 + 15_000 + 175_000) - 360_000  # 130 000
    assert s.besoin_fonds_roulement == (90_000 + 150_000 + 20_000 + 5_000) - (90_000 + 60_000 + 15_000 + 5_000)  # 95 000
    assert s.tresorerie_nette == 60_000 - 25_000  # 35 000
    # Trésorerie nette = FRNG - BFR, pour tout bilan équilibré
    assert s.tresorerie_nette == s.fonds_roulement - s.besoin_fonds_roulement


def test_ratios():
    entreprise = Entreprise("Test", [Exercice(2024, compte_simple(), bilan_simple())])
    r = diagnostiquer(entreprise).dernier.ratios
    assert r.taux_marge_ebe == pytest.approx(0.201)
    assert r.taux_marge_nette == pytest.approx(0.136)
    assert r.autonomie_financiere == pytest.approx(300_000 / 685_000)
    assert r.capacite_remboursement == pytest.approx(200_000 / 172_000)
    assert r.couverture_interets == pytest.approx(20.1)
    assert r.delai_clients == pytest.approx(150_000 / 1_200_000 * 365)
    assert r.liquidite_generale == pytest.approx(325_000 / (90_000 + 60_000 + 15_000 + 25_000))


def test_exercice_court_ramene_a_sa_duree():
    entreprise = Entreprise("Test", [Exercice(2024, compte_simple(), bilan_simple(), duree_mois=6)])
    r = diagnostiquer(entreprise).dernier.ratios
    assert r.delai_clients == pytest.approx(150_000 / 1_200_000 * 182.5)


def test_echelle():
    assert _echelle(0.05, 0.0, 0.10) == pytest.approx(0.5)
    assert _echelle(0.50, 0.0, 0.10) == 1.0
    assert _echelle(-1.0, 0.0, 0.10) == 0.0
    assert _echelle(4.5, 7.0, 2.0) == pytest.approx(0.5)  # échelle inversée
    assert _echelle(None, 0.0, 1.0) is None


def test_division_par_zero():
    entreprise = Entreprise("Vide", [Exercice(2024, CompteDeResultat(), Bilan())])
    d = diagnostiquer(entreprise).dernier
    assert d.ratios.taux_marge_ebe is None
    assert 0 <= d.score.total <= 100


def test_champ_inconnu_refuse():
    with pytest.raises(ValueError, match="chiffre_daffaire"):
        Entreprise.depuis_dict({
            "denomination": "X",
            "exercices": [{"annee": 2024, "compte_de_resultat": {"chiffre_daffaire": 1}, "bilan": {}}],
        })


def test_alerte_moitie_capital():
    bilan = bilan_simple()
    bilan.capitaux_propres = 40_000  # < 100 000 / 2
    bilan.emprunts_dettes_financieres += 260_000  # garde le bilan équilibré
    entreprise = Entreprise("Test", [Exercice(2024, compte_simple(), bilan)])
    codes = {a.code for a in diagnostiquer(entreprise).dernier.alertes}
    assert "capitaux_propres_inferieurs_moitie_capital" in codes


@pytest.mark.parametrize(
    "fichier, notes_attendues",
    [
        ("boulangerie_des_pentes.json", {"A", "B"}),
        ("confluence_negoce.json", {"C"}),
        ("mecanique_precision_rhone.json", {"D", "E"}),
    ],
)
def test_exemples(fichier, notes_attendues):
    entreprise = Entreprise.depuis_json(EXEMPLES / fichier)
    diagnostic = diagnostiquer(entreprise)
    for exercice in entreprise.exercices:
        assert exercice.bilan.ecart_equilibre() < 1e-6
    for analyse in diagnostic.analyses:
        s = analyse.structure
        assert s.tresorerie_nette == pytest.approx(s.fonds_roulement - s.besoin_fonds_roulement)
    assert diagnostic.dernier.score.note in notes_attendues
    assert diagnostic.tableau().shape[1] == len(entreprise.exercices)
