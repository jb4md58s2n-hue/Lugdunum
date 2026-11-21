"""Tests de l'export Excel et de l'interface web."""

import io
from pathlib import Path

import openpyxl
from streamlit.testing.v1 import AppTest

from lugdunum import Entreprise, diagnostiquer
from lugdunum.export import vers_excel

RACINE = Path(__file__).resolve().parent.parent


def test_export_excel():
    entreprise = Entreprise.depuis_json(RACINE / "donnees" / "exemples" / "confluence_negoce.json")
    classeur = openpyxl.load_workbook(io.BytesIO(vers_excel(diagnostiquer(entreprise))))
    assert classeur.sheetnames == ["Synthèse", "Indicateurs", "Alertes"]
    assert classeur["Synthèse"]["B2"].value.startswith("Confluence Négoce")


def test_application_sans_erreur():
    app = AppTest.from_file(str(RACINE / "streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    for nom in app.selectbox[0].options:
        app.selectbox[0].select(nom).run()
        assert not app.exception
        assert app.metric  # les indicateurs clés sont affichés
