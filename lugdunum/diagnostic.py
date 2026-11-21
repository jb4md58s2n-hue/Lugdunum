"""Point d'entrée de l'analyse : produit le diagnostic complet d'une entreprise."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from .modeles import Entreprise, Exercice
from .ratios import Ratios, calculer_ratios
from .score import Alerte, Score, calculer_score, detecter_alertes
from .sig import SIG, calculer_sig
from .structure import StructureFinanciere, calculer_structure


@dataclass(frozen=True)
class AnalyseExercice:
    annee: int
    sig: SIG
    structure: StructureFinanciere
    ratios: Ratios
    croissance_ca: float | None
    score: Score
    alertes: list[Alerte]


@dataclass(frozen=True)
class Diagnostic:
    entreprise: Entreprise
    analyses: list[AnalyseExercice]  # du plus ancien au plus récent

    @property
    def dernier(self) -> AnalyseExercice:
        return self.analyses[-1]

    def tableau(self) -> pd.DataFrame:
        """Tableau des indicateurs, une colonne par exercice."""
        colonnes = {}
        for analyse in self.analyses:
            valeurs = {
                **asdict(analyse.sig),
                **asdict(analyse.structure),
                **asdict(analyse.ratios),
                "croissance_ca": analyse.croissance_ca,
                "score": analyse.score.total,
            }
            colonnes[analyse.annee] = valeurs
        return pd.DataFrame(colonnes)


def _analyser_exercice(exercice: Exercice, precedent: AnalyseExercice | None) -> AnalyseExercice:
    cr, bilan = exercice.compte_de_resultat, exercice.bilan
    sig = calculer_sig(cr)
    structure = calculer_structure(bilan)
    ratios = calculer_ratios(cr, bilan, sig, structure, duree_mois=exercice.duree_mois)

    croissance_ca = None
    if precedent is not None and precedent.sig.chiffre_affaires > 0:
        croissance_ca = sig.chiffre_affaires / precedent.sig.chiffre_affaires - 1

    score = calculer_score(ratios, bilan, sig, croissance_ca)
    alertes = detecter_alertes(
        ratios,
        bilan,
        sig,
        structure,
        croissance_ca=croissance_ca,
        resultat_net_precedent=precedent.sig.resultat_net if precedent else None,
    )
    return AnalyseExercice(
        annee=exercice.annee,
        sig=sig,
        structure=structure,
        ratios=ratios,
        croissance_ca=croissance_ca,
        score=score,
        alertes=alertes,
    )


def diagnostiquer(entreprise: Entreprise) -> Diagnostic:
    if not entreprise.exercices:
        raise ValueError(f"Aucun exercice comptable pour {entreprise.denomination}.")
    analyses: list[AnalyseExercice] = []
    for exercice in entreprise.exercices:
        precedent = analyses[-1] if analyses else None
        # La croissance n'a de sens qu'entre deux exercices consécutifs
        if precedent is not None and exercice.annee - precedent.annee != 1:
            precedent = None
        analyses.append(_analyser_exercice(exercice, precedent))
    return Diagnostic(entreprise=entreprise, analyses=analyses)
