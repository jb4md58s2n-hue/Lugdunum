"""Soldes intermédiaires de gestion (SIG) et capacité d'autofinancement (CAF).

Les définitions suivent le Plan comptable général (PCG).
"""

from __future__ import annotations

from dataclasses import dataclass

from .modeles import CompteDeResultat


@dataclass(frozen=True)
class SIG:
    chiffre_affaires: float
    marge_commerciale: float
    production_exercice: float
    consommations_tiers: float
    valeur_ajoutee: float
    excedent_brut_exploitation: float
    resultat_exploitation: float
    resultat_financier: float
    resultat_courant_avant_impot: float
    resultat_exceptionnel: float
    resultat_net: float
    capacite_autofinancement: float


def calculer_sig(cr: CompteDeResultat) -> SIG:
    chiffre_affaires = cr.ventes_marchandises + cr.production_vendue

    # Marge commerciale = ventes de marchandises - coût d'achat des marchandises vendues
    marge_commerciale = cr.ventes_marchandises - (
        cr.achats_marchandises + cr.variation_stock_marchandises
    )

    production_exercice = (
        cr.production_vendue + cr.production_stockee + cr.production_immobilisee
    )

    # Consommations en provenance des tiers
    consommations_tiers = (
        cr.achats_matieres + cr.variation_stock_matieres + cr.autres_achats_charges_externes
    )

    valeur_ajoutee = marge_commerciale + production_exercice - consommations_tiers

    excedent_brut_exploitation = (
        valeur_ajoutee
        + cr.subventions_exploitation
        - cr.impots_taxes
        - cr.salaires
        - cr.charges_sociales
    )

    resultat_exploitation = (
        excedent_brut_exploitation
        + cr.reprises_et_transferts
        + cr.autres_produits
        - cr.dotations_exploitation
        - cr.autres_charges
    )

    resultat_financier = cr.produits_financiers - cr.charges_financieres
    resultat_courant_avant_impot = resultat_exploitation + resultat_financier
    resultat_exceptionnel = cr.produits_exceptionnels - cr.charges_exceptionnelles

    resultat_net = (
        resultat_courant_avant_impot
        + resultat_exceptionnel
        - cr.participation_salaries
        - cr.impot_benefices
    )

    # CAF, méthode additive simplifiée : résultat net + dotations - reprises d'exploitation.
    # Les dotations/reprises financières et exceptionnelles et les plus-values de cession
    # ne sont pas isolées dans le modèle simplifié de la liasse.
    capacite_autofinancement = (
        resultat_net + cr.dotations_exploitation - cr.reprises_et_transferts
    )

    return SIG(
        chiffre_affaires=chiffre_affaires,
        marge_commerciale=marge_commerciale,
        production_exercice=production_exercice,
        consommations_tiers=consommations_tiers,
        valeur_ajoutee=valeur_ajoutee,
        excedent_brut_exploitation=excedent_brut_exploitation,
        resultat_exploitation=resultat_exploitation,
        resultat_financier=resultat_financier,
        resultat_courant_avant_impot=resultat_courant_avant_impot,
        resultat_exceptionnel=resultat_exceptionnel,
        resultat_net=resultat_net,
        capacite_autofinancement=capacite_autofinancement,
    )
