"""Export du diagnostic au format Excel."""

from __future__ import annotations

import io

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .diagnostic import Diagnostic
from .libelles import INDICATEURS

FORMATS_EXCEL = {
    "euros": '#,##0 "€";-#,##0 "€"',
    "pct": "0.0%",
    "jours": '0 "j"',
    "annees": '0.0 "ans"',
    "fois": "0.00",
    "points": "0",
}


def vers_excel(diagnostic: Diagnostic) -> bytes:
    """Renvoie un classeur Excel : synthèse, indicateurs par exercice, alertes."""
    tableau = diagnostic.tableau()
    entreprise = diagnostic.entreprise
    d = diagnostic.dernier

    tampon = io.BytesIO()
    with pd.ExcelWriter(tampon, engine="openpyxl") as writer:
        # Synthèse
        synthese = pd.DataFrame(
            [
                ("Entreprise", entreprise.denomination + (" (fictive)" if entreprise.fictive else "")),
                ("SIREN", entreprise.siren or ""),
                ("Code NAF", f"{entreprise.code_naf or ''} {entreprise.libelle_naf or ''}".strip()),
                ("Exercice analysé", d.annee),
                ("Score", round(d.score.total)),
                ("Note", d.score.note),
                ("Appréciation", d.score.appreciation),
                ("Rentabilité (/25)", round(d.score.rentabilite, 1)),
                ("Solvabilité (/25)", round(d.score.solvabilite, 1)),
                ("Liquidité (/25)", round(d.score.liquidite, 1)),
                ("Activité (/25)", round(d.score.activite, 1)),
            ],
            columns=["Rubrique", "Valeur"],
        )
        synthese.to_excel(writer, sheet_name="Synthèse", index=False)

        # Indicateurs
        lignes = [cle for cle in INDICATEURS if cle in tableau.index]
        indicateurs = tableau.loc[lignes].copy()
        indicateurs.insert(0, "Groupe", [INDICATEURS[c].groupe for c in lignes])
        indicateurs.insert(1, "Indicateur", [INDICATEURS[c].libelle for c in lignes])
        indicateurs.columns = [str(c) for c in indicateurs.columns]
        indicateurs.to_excel(writer, sheet_name="Indicateurs", index=False)
        feuille = writer.sheets["Indicateurs"]
        for i, cle in enumerate(lignes, start=2):
            for j in range(3, 3 + len(tableau.columns)):
                feuille.cell(row=i, column=j).number_format = FORMATS_EXCEL[INDICATEURS[cle].format]

        # Alertes
        alertes = pd.DataFrame(
            [(a.niveau.value, a.message) for a in d.alertes] or [("", "Aucune alerte")],
            columns=["Niveau", "Alerte"],
        )
        alertes.to_excel(writer, sheet_name="Alertes", index=False)

        for nom, ws in writer.sheets.items():
            for cellule in ws[1]:
                cellule.font = Font(bold=True, color="FFFFFF")
                cellule.fill = PatternFill("solid", fgColor="2A78D6")
            for col in range(1, ws.max_column + 1):
                lettre = get_column_letter(col)
                largeur = max(len(str(c.value or "")) for c in ws[lettre])
                ws.column_dimensions[lettre].width = min(max(12, largeur + 2), 90)
            if nom == "Alertes":
                for cellule in ws["B"]:
                    cellule.alignment = Alignment(wrap_text=True)
    return tampon.getvalue()
