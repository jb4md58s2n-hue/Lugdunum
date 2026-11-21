"""Diagnostic en ligne de commande.

Usage : python -m lugdunum donnees/exemples/boulangerie_des_pentes.json
"""

from __future__ import annotations

import sys

from . import Entreprise, diagnostiquer
from .score import Niveau


def _euros(valeur: float) -> str:
    return f"{valeur:,.0f} €".replace(",", " ")


def _pct(valeur: float | None) -> str:
    return "n.s." if valeur is None else f"{valeur:.1%}"


def _nombre(valeur: float | None, unite: str = "") -> str:
    return "n.s." if valeur is None else f"{valeur:.1f}{unite}"


def afficher(chemin: str) -> None:
    entreprise = Entreprise.depuis_json(chemin)
    diagnostic = diagnostiquer(entreprise)
    d = diagnostic.dernier
    s, r, st = d.sig, d.ratios, d.structure

    titre = entreprise.denomination + (" (entreprise fictive)" if entreprise.fictive else "")
    print("=" * 64)
    print(titre)
    if entreprise.code_naf:
        print(f"NAF {entreprise.code_naf} {entreprise.libelle_naf or ''}".rstrip())
    print(f"Exercice analysé : {d.annee}")
    print("=" * 64)

    print(f"\nSCORE : {d.score.total:.0f}/100, note {d.score.note} ({d.score.appreciation})")
    print(f"  Rentabilité  {d.score.rentabilite:5.1f}/25")
    print(f"  Solvabilité  {d.score.solvabilite:5.1f}/25")
    print(f"  Liquidité    {d.score.liquidite:5.1f}/25")
    print(f"  Activité     {d.score.activite:5.1f}/25")

    print("\nSOLDES INTERMÉDIAIRES DE GESTION")
    print(f"  Chiffre d'affaires      {_euros(s.chiffre_affaires):>15}   croissance {_pct(d.croissance_ca)}")
    print(f"  Valeur ajoutée          {_euros(s.valeur_ajoutee):>15}")
    print(f"  EBE                     {_euros(s.excedent_brut_exploitation):>15}   marge {_pct(r.taux_marge_ebe)}")
    print(f"  Résultat d'exploitation {_euros(s.resultat_exploitation):>15}")
    print(f"  Résultat net            {_euros(s.resultat_net):>15}   marge {_pct(r.taux_marge_nette)}")
    print(f"  CAF                     {_euros(s.capacite_autofinancement):>15}")

    print("\nSTRUCTURE FINANCIÈRE")
    print(f"  Fonds de roulement      {_euros(st.fonds_roulement):>15}")
    print(f"  BFR                     {_euros(st.besoin_fonds_roulement):>15}   {_nombre(r.bfr_jours_ca, ' j de CA')}")
    print(f"  Trésorerie nette        {_euros(st.tresorerie_nette):>15}")

    print("\nRATIOS CLÉS")
    print(f"  Autonomie financière    {_pct(r.autonomie_financiere)}")
    print(f"  Capacité remboursement  {_nombre(r.capacite_remboursement, ' ans')}")
    print(f"  Liquidité générale      {_nombre(r.liquidite_generale)}")
    print(f"  Délai clients           {_nombre(r.delai_clients, ' j')}")
    print(f"  Délai fournisseurs      {_nombre(r.delai_fournisseurs, ' j')}")
    print(f"  ROE                     {_pct(r.rentabilite_capitaux_propres)}")

    print("\nALERTES")
    if not d.alertes:
        print("  Aucune alerte.")
    symboles = {Niveau.CRITIQUE: "[!!]", Niveau.ATTENTION: "[! ]", Niveau.INFO: "[i ]"}
    for alerte in d.alertes:
        print(f"  {symboles[alerte.niveau]} {alerte.message}")
    print()


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for chemin in sys.argv[1:]:
        afficher(chemin)


if __name__ == "__main__":
    main()
