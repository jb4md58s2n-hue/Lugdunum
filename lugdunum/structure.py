"""Analyse fonctionnelle du bilan : FRNG, BFR et trésorerie nette.

Relation fondamentale : trésorerie nette = FRNG - BFR.
"""

from __future__ import annotations

from dataclasses import dataclass

from .modeles import Bilan


@dataclass(frozen=True)
class StructureFinanciere:
    ressources_stables: float
    emplois_stables: float
    fonds_roulement: float  # FRNG
    besoin_fonds_roulement: float  # BFR
    tresorerie_nette: float
    dettes_financieres_nettes: float  # dettes financières - disponibilités
    dettes_court_terme: float


def calculer_structure(bilan: Bilan) -> StructureFinanciere:
    dettes_financieres_stables = bilan.emprunts_dettes_financieres - bilan.dont_concours_bancaires

    ressources_stables = (
        bilan.capitaux_propres + bilan.provisions_risques_charges + dettes_financieres_stables
    )
    emplois_stables = bilan.actif_immobilise
    fonds_roulement = ressources_stables - emplois_stables

    actif_circulant_exploitation = (
        bilan.stocks
        + bilan.creances_clients
        + bilan.autres_creances
        + bilan.charges_constatees_avance
    )
    dettes_non_financieres = (
        bilan.dettes_fournisseurs
        + bilan.dettes_fiscales_sociales
        + bilan.autres_dettes
        + bilan.produits_constates_avance
    )
    besoin_fonds_roulement = actif_circulant_exploitation - dettes_non_financieres

    tresorerie_nette = bilan.disponibilites - bilan.dont_concours_bancaires

    dettes_court_terme = (
        bilan.dettes_fournisseurs
        + bilan.dettes_fiscales_sociales
        + bilan.autres_dettes
        + bilan.dont_concours_bancaires
    )

    return StructureFinanciere(
        ressources_stables=ressources_stables,
        emplois_stables=emplois_stables,
        fonds_roulement=fonds_roulement,
        besoin_fonds_roulement=besoin_fonds_roulement,
        tresorerie_nette=tresorerie_nette,
        dettes_financieres_nettes=bilan.emprunts_dettes_financieres - bilan.disponibilites,
        dettes_court_terme=dettes_court_terme,
    )
