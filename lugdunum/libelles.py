"""Libellés et formats d'affichage des indicateurs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Indicateur:
    libelle: str
    format: str  # "euros", "pct", "jours", "fois", "annees", "points"
    groupe: str
    aide: str = ""


INDICATEURS: dict[str, Indicateur] = {
    # SIG
    "chiffre_affaires": Indicateur("Chiffre d'affaires", "euros", "SIG"),
    "marge_commerciale": Indicateur("Marge commerciale", "euros", "SIG", "Ventes de marchandises − coût d'achat des marchandises vendues"),
    "production_exercice": Indicateur("Production de l'exercice", "euros", "SIG"),
    "consommations_tiers": Indicateur("Consommations en provenance des tiers", "euros", "SIG"),
    "valeur_ajoutee": Indicateur("Valeur ajoutée", "euros", "SIG", "Richesse créée par l'entreprise"),
    "excedent_brut_exploitation": Indicateur("Excédent brut d'exploitation (EBE)", "euros", "SIG", "Performance économique, avant politique d'investissement et de financement"),
    "resultat_exploitation": Indicateur("Résultat d'exploitation", "euros", "SIG"),
    "resultat_financier": Indicateur("Résultat financier", "euros", "SIG"),
    "resultat_courant_avant_impot": Indicateur("Résultat courant avant impôt", "euros", "SIG"),
    "resultat_exceptionnel": Indicateur("Résultat exceptionnel", "euros", "SIG"),
    "resultat_net": Indicateur("Résultat net", "euros", "SIG"),
    "capacite_autofinancement": Indicateur("Capacité d'autofinancement (CAF)", "euros", "SIG", "Ressource interne dégagée par l'activité"),
    "croissance_ca": Indicateur("Croissance du chiffre d'affaires", "pct", "SIG"),
    # Bilan fonctionnel
    "ressources_stables": Indicateur("Ressources stables", "euros", "Bilan fonctionnel"),
    "emplois_stables": Indicateur("Emplois stables (actif immobilisé)", "euros", "Bilan fonctionnel"),
    "fonds_roulement": Indicateur("Fonds de roulement net global (FRNG)", "euros", "Bilan fonctionnel", "Ressources stables − emplois stables"),
    "besoin_fonds_roulement": Indicateur("Besoin en fonds de roulement (BFR)", "euros", "Bilan fonctionnel", "Argent immobilisé par le cycle d'exploitation"),
    "tresorerie_nette": Indicateur("Trésorerie nette", "euros", "Bilan fonctionnel", "FRNG − BFR"),
    "dettes_financieres_nettes": Indicateur("Dettes financières nettes", "euros", "Bilan fonctionnel"),
    "dettes_court_terme": Indicateur("Dettes à court terme", "euros", "Bilan fonctionnel"),
    # Rentabilité
    "taux_marge_ebe": Indicateur("Taux de marge d'EBE", "pct", "Rentabilité", "EBE / CA"),
    "taux_marge_nette": Indicateur("Taux de marge nette", "pct", "Rentabilité", "Résultat net / CA"),
    "taux_valeur_ajoutee": Indicateur("Taux de valeur ajoutée", "pct", "Rentabilité", "VA / CA"),
    "rentabilite_capitaux_propres": Indicateur("Rentabilité des capitaux propres (ROE)", "pct", "Rentabilité", "Résultat net / capitaux propres"),
    "rentabilite_economique": Indicateur("Rentabilité économique", "pct", "Rentabilité", "Résultat d'exploitation / (capitaux propres + dettes financières)"),
    "poids_charges_personnel": Indicateur("Poids des charges de personnel", "pct", "Rentabilité", "Charges de personnel / VA"),
    # Solvabilité
    "autonomie_financiere": Indicateur("Autonomie financière", "pct", "Solvabilité", "Capitaux propres / total du bilan"),
    "gearing": Indicateur("Gearing", "fois", "Solvabilité", "Dettes financières nettes / capitaux propres"),
    "capacite_remboursement": Indicateur("Capacité de remboursement", "annees", "Solvabilité", "Dettes financières / CAF"),
    "couverture_interets": Indicateur("Couverture des intérêts", "fois", "Solvabilité", "EBE / charges d'intérêts"),
    # Liquidité
    "liquidite_generale": Indicateur("Liquidité générale", "fois", "Liquidité", "Actif circulant / dettes à court terme"),
    "liquidite_reduite": Indicateur("Liquidité réduite", "fois", "Liquidité", "(Actif circulant − stocks) / dettes à court terme"),
    "tresorerie_jours_ca": Indicateur("Trésorerie en jours de CA", "jours", "Liquidité"),
    # Cycle d'exploitation
    "delai_clients": Indicateur("Délai de paiement clients (DSO)", "jours", "Cycle d'exploitation"),
    "delai_fournisseurs": Indicateur("Délai de paiement fournisseurs (DPO)", "jours", "Cycle d'exploitation"),
    "rotation_stocks": Indicateur("Rotation des stocks", "jours", "Cycle d'exploitation"),
    "bfr_jours_ca": Indicateur("BFR en jours de CA", "jours", "Cycle d'exploitation"),
    # Score
    "score": Indicateur("Score Lugdunum", "points", "Score"),
}


def formater(valeur: float | None, format: str) -> str:
    """Formate une valeur pour l'affichage, à la française."""
    if valeur is None:
        return "n.s."
    if format == "euros":
        return f"{valeur:,.0f} €".replace(",", " ")
    if format == "pct":
        return f"{valeur:.1%}".replace(".", ",").replace("%", " %")
    if format == "jours":
        return f"{valeur:.0f} j"
    if format == "annees":
        return f"{valeur:.1f} ans".replace(".", ",")
    if format == "fois":
        return f"{valeur:.2f}".replace(".", ",")
    if format == "points":
        return f"{valeur:.0f}/100"
    return str(valeur)
