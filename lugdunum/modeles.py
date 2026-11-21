"""Modèle de données : les comptes annuels d'une entreprise.

Les postes reprennent ceux de la liasse fiscale du régime réel normal
(formulaires 2050 à 2053), sous une forme simplifiée. Tous les montants
sont exprimés en euros.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any


@dataclass
class CompteDeResultat:
    """Compte de résultat (liasse 2052-2053)."""

    # Produits d'exploitation
    ventes_marchandises: float = 0.0
    production_vendue: float = 0.0  # biens et services
    production_stockee: float = 0.0
    production_immobilisee: float = 0.0
    subventions_exploitation: float = 0.0
    reprises_et_transferts: float = 0.0  # reprises sur amortissements/provisions, transferts de charges
    autres_produits: float = 0.0

    # Charges d'exploitation
    achats_marchandises: float = 0.0
    variation_stock_marchandises: float = 0.0  # stock initial - stock final
    achats_matieres: float = 0.0  # matières premières et autres approvisionnements
    variation_stock_matieres: float = 0.0  # stock initial - stock final
    autres_achats_charges_externes: float = 0.0
    impots_taxes: float = 0.0
    salaires: float = 0.0
    charges_sociales: float = 0.0
    dotations_exploitation: float = 0.0  # amortissements et provisions
    autres_charges: float = 0.0

    # Financier
    produits_financiers: float = 0.0
    charges_financieres: float = 0.0
    dont_interets: float = 0.0  # intérêts et charges assimilées, inclus dans charges_financieres

    # Exceptionnel
    produits_exceptionnels: float = 0.0
    charges_exceptionnelles: float = 0.0

    # Répartition
    participation_salaries: float = 0.0
    impot_benefices: float = 0.0


@dataclass
class Bilan:
    """Bilan en valeurs nettes (liasse 2050-2051)."""

    # Actif
    immobilisations_incorporelles: float = 0.0
    immobilisations_corporelles: float = 0.0
    immobilisations_financieres: float = 0.0
    stocks: float = 0.0  # tous stocks et en-cours
    creances_clients: float = 0.0
    autres_creances: float = 0.0
    disponibilites: float = 0.0  # y compris valeurs mobilières de placement
    charges_constatees_avance: float = 0.0

    # Passif
    capital_social: float = 0.0  # inclus dans capitaux_propres
    capitaux_propres: float = 0.0  # y compris résultat de l'exercice
    provisions_risques_charges: float = 0.0
    emprunts_dettes_financieres: float = 0.0  # y compris concours bancaires courants
    dont_concours_bancaires: float = 0.0  # découverts, inclus dans emprunts_dettes_financieres
    dettes_fournisseurs: float = 0.0
    dettes_fiscales_sociales: float = 0.0
    autres_dettes: float = 0.0
    produits_constates_avance: float = 0.0

    @property
    def actif_immobilise(self) -> float:
        return (
            self.immobilisations_incorporelles
            + self.immobilisations_corporelles
            + self.immobilisations_financieres
        )

    @property
    def actif_circulant(self) -> float:
        return (
            self.stocks
            + self.creances_clients
            + self.autres_creances
            + self.disponibilites
            + self.charges_constatees_avance
        )

    @property
    def total_actif(self) -> float:
        return self.actif_immobilise + self.actif_circulant

    @property
    def total_passif(self) -> float:
        return (
            self.capitaux_propres
            + self.provisions_risques_charges
            + self.emprunts_dettes_financieres
            + self.dettes_fournisseurs
            + self.dettes_fiscales_sociales
            + self.autres_dettes
            + self.produits_constates_avance
        )

    def ecart_equilibre(self) -> float:
        """Écart relatif entre total actif et total passif (0 si le bilan est équilibré)."""
        reference = max(abs(self.total_actif), abs(self.total_passif), 1.0)
        return abs(self.total_actif - self.total_passif) / reference


@dataclass
class Exercice:
    """Un exercice comptable : compte de résultat et bilan de clôture."""

    annee: int
    compte_de_resultat: CompteDeResultat
    bilan: Bilan
    duree_mois: int = 12


@dataclass
class Entreprise:
    """Une entreprise et l'historique de ses comptes annuels."""

    denomination: str
    exercices: list[Exercice] = field(default_factory=list)
    siren: str | None = None
    code_naf: str | None = None
    libelle_naf: str | None = None
    fictive: bool = False  # True pour les jeux de données d'exemple

    def __post_init__(self) -> None:
        self.exercices.sort(key=lambda e: e.annee)

    # --- Import / export -------------------------------------------------

    @classmethod
    def depuis_dict(cls, donnees: dict[str, Any]) -> Entreprise:
        donnees = dict(donnees)
        exercices = [_exercice_depuis_dict(e) for e in donnees.pop("exercices", [])]
        _verifier_champs(cls, donnees, ignorer={"exercices"})
        return cls(exercices=exercices, **donnees)

    @classmethod
    def depuis_json(cls, chemin: str | Path) -> Entreprise:
        with open(chemin, encoding="utf-8") as f:
            return cls.depuis_dict(json.load(f))

    def vers_dict(self) -> dict[str, Any]:
        return asdict(self)


def _verifier_champs(classe: type, donnees: dict[str, Any], ignorer: set[str] = frozenset()) -> None:
    """Refuse les champs inconnus, pour repérer les fautes de frappe dans les fichiers."""
    connus = {f.name for f in fields(classe)} | ignorer
    inconnus = set(donnees) - connus
    if inconnus:
        raise ValueError(
            f"Champ(s) inconnu(s) pour {classe.__name__} : {', '.join(sorted(inconnus))}"
        )


def _exercice_depuis_dict(donnees: dict[str, Any]) -> Exercice:
    donnees = dict(donnees)
    cr = donnees.pop("compte_de_resultat", {})
    bilan = donnees.pop("bilan", {})
    _verifier_champs(CompteDeResultat, cr)
    _verifier_champs(Bilan, bilan)
    _verifier_champs(Exercice, donnees, ignorer={"compte_de_resultat", "bilan"})
    return Exercice(
        compte_de_resultat=CompteDeResultat(**cr),
        bilan=Bilan(**bilan),
        **donnees,
    )
