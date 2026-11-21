"""Lugdunum : diagnostic financier automatisé des PME françaises."""

from .diagnostic import Diagnostic, diagnostiquer
from .modeles import Bilan, CompteDeResultat, Entreprise, Exercice

__all__ = [
    "Bilan",
    "CompteDeResultat",
    "Diagnostic",
    "Entreprise",
    "Exercice",
    "diagnostiquer",
]

__version__ = "0.1.0"
