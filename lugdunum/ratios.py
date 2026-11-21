"""Ratios financiers : rentabilité, solvabilité, liquidité et gestion du cycle d'exploitation.

Un ratio vaut ``None`` quand il n'est pas calculable (division par zéro).
"""

from __future__ import annotations

from dataclasses import dataclass

from .modeles import Bilan, CompteDeResultat
from .sig import SIG
from .structure import StructureFinanciere

TAUX_TVA_DEFAUT = 0.20


def _div(numerateur: float, denominateur: float) -> float | None:
    if denominateur == 0:
        return None
    return numerateur / denominateur


@dataclass(frozen=True)
class Ratios:
    # Rentabilité
    taux_marge_ebe: float | None  # EBE / CA
    taux_marge_nette: float | None  # résultat net / CA
    taux_valeur_ajoutee: float | None  # VA / CA
    rentabilite_capitaux_propres: float | None  # ROE : résultat net / capitaux propres
    rentabilite_economique: float | None  # résultat d'exploitation / (capitaux propres + dettes financières)
    poids_charges_personnel: float | None  # (salaires + charges sociales) / VA

    # Solvabilité
    autonomie_financiere: float | None  # capitaux propres / total bilan
    gearing: float | None  # dettes financières nettes / capitaux propres
    capacite_remboursement: float | None  # dettes financières / CAF, en années
    couverture_interets: float | None  # EBE / intérêts

    # Liquidité
    liquidite_generale: float | None  # actif circulant / dettes à court terme
    liquidite_reduite: float | None  # (actif circulant - stocks) / dettes à court terme
    tresorerie_jours_ca: float | None  # trésorerie nette en jours de CA

    # Cycle d'exploitation (en jours)
    delai_clients: float | None  # DSO
    delai_fournisseurs: float | None  # DPO
    rotation_stocks: float | None  # DIO
    bfr_jours_ca: float | None


def calculer_ratios(
    cr: CompteDeResultat,
    bilan: Bilan,
    sig: SIG,
    structure: StructureFinanciere,
    duree_mois: int = 12,
    taux_tva: float = TAUX_TVA_DEFAUT,
) -> Ratios:
    ca = sig.chiffre_affaires
    jours = 365 * duree_mois / 12  # les délais sont rapportés à la durée réelle de l'exercice
    charges_personnel = cr.salaires + cr.charges_sociales
    achats_consommes = (
        cr.achats_marchandises
        + cr.variation_stock_marchandises
        + cr.achats_matieres
        + cr.variation_stock_matieres
    )
    achats_ttc = (
        cr.achats_marchandises + cr.achats_matieres + cr.autres_achats_charges_externes
    ) * (1 + taux_tva)

    # Capacité de remboursement : non significative si la CAF est négative ou nulle
    if bilan.emprunts_dettes_financieres == 0:
        capacite_remboursement = 0.0
    elif sig.capacite_autofinancement <= 0:
        capacite_remboursement = None
    else:
        capacite_remboursement = bilan.emprunts_dettes_financieres / sig.capacite_autofinancement

    delai_clients = _div(bilan.creances_clients, ca * (1 + taux_tva))
    delai_fournisseurs = _div(bilan.dettes_fournisseurs, achats_ttc)
    rotation_stocks = _div(bilan.stocks, achats_consommes) if bilan.stocks else None
    tresorerie_jours = _div(structure.tresorerie_nette, ca)
    bfr_jours = _div(structure.besoin_fonds_roulement, ca)

    return Ratios(
        taux_marge_ebe=_div(sig.excedent_brut_exploitation, ca),
        taux_marge_nette=_div(sig.resultat_net, ca),
        taux_valeur_ajoutee=_div(sig.valeur_ajoutee, ca),
        rentabilite_capitaux_propres=(
            _div(sig.resultat_net, bilan.capitaux_propres) if bilan.capitaux_propres > 0 else None
        ),
        rentabilite_economique=_div(
            sig.resultat_exploitation,
            bilan.capitaux_propres + bilan.emprunts_dettes_financieres,
        ),
        poids_charges_personnel=_div(charges_personnel, sig.valeur_ajoutee),
        autonomie_financiere=_div(bilan.capitaux_propres, bilan.total_passif),
        gearing=(
            _div(structure.dettes_financieres_nettes, bilan.capitaux_propres)
            if bilan.capitaux_propres > 0
            else None
        ),
        capacite_remboursement=capacite_remboursement,
        couverture_interets=_div(sig.excedent_brut_exploitation, cr.dont_interets),
        liquidite_generale=_div(bilan.actif_circulant, structure.dettes_court_terme),
        liquidite_reduite=_div(bilan.actif_circulant - bilan.stocks, structure.dettes_court_terme),
        tresorerie_jours_ca=tresorerie_jours * jours if tresorerie_jours is not None else None,
        delai_clients=delai_clients * jours if delai_clients is not None else None,
        delai_fournisseurs=delai_fournisseurs * jours if delai_fournisseurs is not None else None,
        rotation_stocks=rotation_stocks * jours if rotation_stocks is not None else None,
        bfr_jours_ca=bfr_jours * jours if bfr_jours is not None else None,
    )
