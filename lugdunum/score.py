"""Score de santé financière Lugdunum (0 à 100) et alertes.

Le score agrège quatre axes notés chacun sur 25 points :
rentabilité, solvabilité, liquidité, activité et cycle d'exploitation.

Les seuils sont des repères usuels de l'analyse financière, pas un modèle de
défaillance calibré statistiquement. Ils ne tiennent pas encore compte du secteur.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .modeles import Bilan
from .ratios import Ratios
from .sig import SIG
from .structure import StructureFinanciere

POINTS_PAR_AXE = 25.0


def _fr(valeur: float) -> str:
    """Nombre à une décimale, avec la virgule française."""
    return f"{valeur:.1f}".replace(".", ",")


def _echelle(valeur: float | None, zero: float, plein: float) -> float | None:
    """Convertit une valeur en note entre 0 et 1, linéairement entre deux seuils.

    ``zero`` donne 0, ``plein`` donne 1. Si ``zero > plein``, une valeur faible est meilleure.
    """
    if valeur is None:
        return None
    note = (valeur - zero) / (plein - zero)
    return max(0.0, min(1.0, note))


def _moyenne_ponderee(composantes: list[tuple[float | None, float]]) -> float:
    """Moyenne pondérée des composantes calculables ; 0,5 (neutre) si aucune ne l'est."""
    disponibles = [(note, poids) for note, poids in composantes if note is not None]
    if not disponibles:
        return 0.5
    total_poids = sum(poids for _, poids in disponibles)
    return sum(note * poids for note, poids in disponibles) / total_poids


@dataclass(frozen=True)
class Score:
    rentabilite: float
    solvabilite: float
    liquidite: float
    activite: float

    @property
    def total(self) -> float:
        return self.rentabilite + self.solvabilite + self.liquidite + self.activite

    @property
    def note(self) -> str:
        total = self.total
        if total >= 80:
            return "A"
        if total >= 65:
            return "B"
        if total >= 50:
            return "C"
        if total >= 35:
            return "D"
        return "E"

    @property
    def appreciation(self) -> str:
        return {
            "A": "Situation financière très solide",
            "B": "Situation financière saine",
            "C": "Situation correcte, avec des points de vigilance",
            "D": "Situation fragile",
            "E": "Situation critique",
        }[self.note]


def calculer_score(
    ratios: Ratios,
    bilan: Bilan,
    sig: SIG,
    croissance_ca: float | None = None,
) -> Score:
    rentabilite = _moyenne_ponderee([
        (_echelle(ratios.taux_marge_ebe, 0.0, 0.10), 0.5),
        (_echelle(ratios.taux_marge_nette, -0.02, 0.05), 0.5),
    ])

    # Capacité de remboursement : None signifie une CAF négative avec des dettes -> note nulle
    if ratios.capacite_remboursement is None and bilan.emprunts_dettes_financieres > 0:
        note_remboursement: float | None = 0.0
    else:
        note_remboursement = _echelle(ratios.capacite_remboursement, 7.0, 2.0)
    autonomie = ratios.autonomie_financiere if bilan.capitaux_propres > 0 else 0.0
    solvabilite = _moyenne_ponderee([
        (_echelle(autonomie, 0.05, 0.40), 0.5),
        (note_remboursement, 0.5),
    ])

    liquidite = _moyenne_ponderee([
        (_echelle(ratios.liquidite_generale, 0.8, 1.5), 0.5),
        (_echelle(ratios.tresorerie_jours_ca, -15.0, 30.0), 0.5),
    ])

    activite = _moyenne_ponderee([
        (_echelle(croissance_ca, -0.10, 0.10), 0.5),
        (_echelle(ratios.delai_clients, 90.0, 30.0), 0.5),
    ])

    return Score(
        rentabilite=rentabilite * POINTS_PAR_AXE,
        solvabilite=solvabilite * POINTS_PAR_AXE,
        liquidite=liquidite * POINTS_PAR_AXE,
        activite=activite * POINTS_PAR_AXE,
    )


class Niveau(str, Enum):
    CRITIQUE = "critique"
    ATTENTION = "attention"
    INFO = "info"


@dataclass(frozen=True)
class Alerte:
    niveau: Niveau
    code: str
    message: str


def detecter_alertes(
    ratios: Ratios,
    bilan: Bilan,
    sig: SIG,
    structure: StructureFinanciere,
    croissance_ca: float | None = None,
    resultat_net_precedent: float | None = None,
) -> list[Alerte]:
    alertes: list[Alerte] = []

    def ajouter(niveau: Niveau, code: str, message: str) -> None:
        alertes.append(Alerte(niveau, code, message))

    # Qualité des données
    if bilan.ecart_equilibre() > 0.01:
        ajouter(
            Niveau.INFO,
            "bilan_desequilibre",
            "Le total de l'actif ne correspond pas au total du passif : "
            "certains postes du bilan sont peut-être incomplets.",
        )

    # Capitaux propres
    if bilan.capitaux_propres <= 0:
        ajouter(
            Niveau.CRITIQUE,
            "capitaux_propres_negatifs",
            "Les capitaux propres sont négatifs ou nuls : l'entreprise a perdu "
            "l'intégralité de ses fonds propres.",
        )
    elif bilan.capital_social > 0 and bilan.capitaux_propres < bilan.capital_social / 2:
        ajouter(
            Niveau.CRITIQUE,
            "capitaux_propres_inferieurs_moitie_capital",
            "Les capitaux propres sont inférieurs à la moitié du capital social : "
            "les associés doivent se prononcer sur la poursuite de l'activité "
            "(art. L223-42 et L225-248 du Code de commerce).",
        )

    # Rentabilité
    if sig.excedent_brut_exploitation < 0:
        ajouter(
            Niveau.CRITIQUE,
            "ebe_negatif",
            "L'EBE est négatif : l'activité courante ne couvre pas ses propres charges.",
        )
    if sig.resultat_net < 0:
        if resultat_net_precedent is not None and resultat_net_precedent < 0:
            ajouter(
                Niveau.CRITIQUE,
                "pertes_repetees",
                "L'entreprise est en perte pour le deuxième exercice consécutif.",
            )
        else:
            ajouter(Niveau.ATTENTION, "perte", "L'exercice se solde par une perte.")

    # Solvabilité
    if bilan.emprunts_dettes_financieres > 0:
        if sig.capacite_autofinancement <= 0:
            ajouter(
                Niveau.CRITIQUE,
                "caf_negative",
                "La CAF est négative alors que l'entreprise est endettée : "
                "elle ne peut pas rembourser ses dettes avec son activité.",
            )
        elif ratios.capacite_remboursement is not None and ratios.capacite_remboursement > 4:
            ajouter(
                Niveau.ATTENTION,
                "endettement_eleve",
                f"Il faudrait {_fr(ratios.capacite_remboursement)} années de CAF pour rembourser "
                "les dettes financières (les banques regardent en général un plafond de 3 à 4 ans).",
            )
    # Si l'EBE est négatif, l'alerte « EBE négatif » suffit
    if ratios.couverture_interets is not None and 0 <= ratios.couverture_interets < 3:
        ajouter(
            Niveau.ATTENTION,
            "couverture_interets_faible",
            f"L'EBE ne couvre que {_fr(ratios.couverture_interets)} fois les intérêts d'emprunt.",
        )

    # Liquidité
    if structure.tresorerie_nette < 0:
        ajouter(
            Niveau.ATTENTION,
            "tresorerie_negative",
            "La trésorerie nette est négative : l'entreprise dépend de ses découverts bancaires.",
        )
    if ratios.liquidite_generale is not None and ratios.liquidite_generale < 1:
        ajouter(
            Niveau.ATTENTION,
            "liquidite_insuffisante",
            "L'actif circulant ne couvre pas les dettes à court terme (liquidité générale < 1).",
        )

    # Activité et cycle d'exploitation
    if ratios.delai_clients is not None and ratios.delai_clients > 60:
        ajouter(
            Niveau.ATTENTION,
            "delai_clients_long",
            f"Les clients paient en {ratios.delai_clients:.0f} jours en moyenne, au-delà du "
            "délai légal de 60 jours (art. L441-10 du Code de commerce).",
        )
    if croissance_ca is not None and croissance_ca < -0.10:
        ajouter(
            Niveau.ATTENTION,
            "baisse_activite",
            f"Le chiffre d'affaires recule de {abs(croissance_ca) * 100:.0f}\u202f% sur un an.",
        )

    ordre = {Niveau.CRITIQUE: 0, Niveau.ATTENTION: 1, Niveau.INFO: 2}
    return sorted(alertes, key=lambda a: ordre[a.niveau])
