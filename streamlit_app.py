"""Interface web de Lugdunum.

Lancement : streamlit run streamlit_app.py
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lugdunum import Bilan, CompteDeResultat, Entreprise, diagnostiquer
from lugdunum.diagnostic import AnalyseExercice, Diagnostic
from lugdunum.export import vers_excel
from lugdunum.libelles import INDICATEURS, formater
from lugdunum.score import Niveau

RACINE = Path(__file__).resolve().parent
EXEMPLES = RACINE / "donnees" / "exemples"

# Palette (validée pour la lisibilité, y compris en cas de daltonisme)
BLEU, ORANGE, VERT_EAU, ROUGE = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
ENCRE, ENCRE_2, ENCRE_MUETTE = "#0b0b0b", "#52514e", "#898781"
GRILLE, AXE = "#e1e0d9", "#c3c2b7"
STATUTS = {  # note -> (couleur, libellé)
    "A": ("#0ca30c", "Très solide"),
    "B": ("#0ca30c", "Saine"),
    "C": ("#fab219", "Vigilance"),
    "D": ("#ec835a", "Fragile"),
    "E": ("#d03b3b", "Critique"),
}
POLICE = 'system-ui, -apple-system, "Segoe UI", sans-serif'

st.set_page_config(
    page_title="Lugdunum : diagnostic financier",
    page_icon=":material/monitoring:",
    layout="wide",
)

st.markdown(
    f"""
    <style>
      .block-container {{ padding-top: 2rem; max-width: 1200px; }}
      .carte {{ background: #ffffff; border: 1px solid rgba(11,11,11,0.10); border-radius: 12px;
                padding: 1.25rem 1.5rem; height: 100%; }}
      .score-ligne {{ display: flex; align-items: baseline; gap: .6rem; }}
      .score-valeur {{ font-size: 3.6rem; font-weight: 700; line-height: 1; color: {ENCRE}; }}
      .score-sur {{ font-size: 1.1rem; color: {ENCRE_MUETTE}; }}
      .pastille {{ display: inline-flex; align-items: center; gap: .45rem; margin-top: .9rem;
                   font-weight: 600; color: {ENCRE}; }}
      .pastille .lettre {{ display: inline-flex; width: 1.9rem; height: 1.9rem; border-radius: 6px;
                           align-items: center; justify-content: center; font-weight: 700; }}
      .appreciation {{ color: {ENCRE_2}; margin-top: .4rem; font-size: .95rem; }}
      .axe {{ margin-bottom: .85rem; }}
      .axe-entete {{ display: flex; justify-content: space-between; font-size: .92rem; color: {ENCRE_2};
                     margin-bottom: .3rem; }}
      .axe-entete b {{ color: {ENCRE}; font-weight: 600; font-variant-numeric: tabular-nums; }}
      .jauge {{ background: #f0efec; border-radius: 4px; height: 8px; overflow: hidden; }}
      .jauge > div {{ background: {BLEU}; height: 100%; border-radius: 4px; }}
      .etiquette-fictive {{ display: inline-block; background: #f0efec; color: {ENCRE_2};
                            border-radius: 999px; padding: .15rem .7rem; font-size: .8rem;
                            margin-left: .5rem; vertical-align: middle; }}
      .sous-titre {{ color: {ENCRE_2}; margin-top: -.6rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Données ---------------------------------------------------------------

@st.cache_data
def exemples_disponibles() -> dict[str, str]:
    """Dénomination -> chemin du fichier d'exemple."""
    resultat = {}
    for chemin in sorted(EXEMPLES.glob("*.json")):
        with open(chemin, encoding="utf-8") as f:
            resultat[json.load(f)["denomination"]] = str(chemin)
    return resultat


def modele_vierge() -> str:
    modele = {
        "denomination": "Nom de l'entreprise",
        "siren": "",
        "code_naf": "",
        "libelle_naf": "",
        "exercices": [
            {
                "annee": 2024,
                "duree_mois": 12,
                "compte_de_resultat": asdict(CompteDeResultat()),
                "bilan": asdict(Bilan()),
            }
        ],
    }
    return json.dumps(modele, ensure_ascii=False, indent=2)


# --- Graphiques ------------------------------------------------------------

def styliser(fig: go.Figure, hauteur: int = 340, format_y: str = ",.0f", suffixe_y: str = "") -> go.Figure:
    fig.update_layout(
        template="none",
        height=hauteur,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=POLICE, color=ENCRE_2, size=13),
        margin=dict(l=8, r=8, t=36, b=8),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="left", x=0, title=None),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=AXE, font=dict(family=POLICE, color=ENCRE)),
        separators=", ",
        bargap=0.35,
        bargroupgap=0.12,
    )
    fig.update_xaxes(showgrid=False, linecolor=AXE, ticks="", type="category")
    fig.update_yaxes(
        gridcolor=GRILLE, zerolinecolor=AXE, zerolinewidth=1, linecolor=AXE,
        tickformat=format_y, ticksuffix=suffixe_y,
    )
    return fig


def graphique_chiffre_affaires(diag: Diagnostic) -> go.Figure:
    annees = [str(a.annee) for a in diag.analyses]
    ca = [a.sig.chiffre_affaires for a in diag.analyses]
    etiquettes = [
        "" if a.croissance_ca is None else formater(a.croissance_ca, "pct").replace("-", "−")
        for a in diag.analyses
    ]
    etiquettes = [("+" + e if e and not e.startswith("−") else e) for e in etiquettes]
    fig = go.Figure(go.Bar(
        x=annees, y=ca, marker=dict(color=BLEU, cornerradius=4), width=0.45,
        text=etiquettes, textposition="outside", textfont=dict(color=ENCRE_2),
        hovertemplate="%{x}<br>Chiffre d'affaires : %{y:,.0f} €<extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(title=dict(text="Chiffre d'affaires et croissance", font=dict(color=ENCRE, size=15)))
    return styliser(fig, suffixe_y=" €")


def graphique_marges(diag: Diagnostic) -> go.Figure:
    annees = [str(a.annee) for a in diag.analyses]
    fig = go.Figure()
    for nom, cle, couleur in [
        ("Marge d'EBE", "taux_marge_ebe", BLEU),
        ("Marge nette", "taux_marge_nette", ORANGE),
    ]:
        valeurs = [getattr(a.ratios, cle) for a in diag.analyses]
        fig.add_trace(go.Scatter(
            x=annees, y=valeurs, name=nom, mode="lines+markers",
            line=dict(color=couleur, width=2), marker=dict(size=9, color=couleur, line=dict(color="#ffffff", width=2)),
            hovertemplate=f"{nom} : %{{y:.1%}}<extra></extra>",
        ))
    fig.update_layout(title=dict(text="Marges", font=dict(color=ENCRE, size=15)), hovermode="x unified")
    return styliser(fig, format_y=".0%")


def graphique_structure(diag: Diagnostic) -> go.Figure:
    annees = [str(a.annee) for a in diag.analyses]
    fig = go.Figure()
    for nom, cle, couleur in [
        ("Fonds de roulement", "fonds_roulement", BLEU),
        ("BFR", "besoin_fonds_roulement", ORANGE),
        ("Trésorerie nette", "tresorerie_nette", VERT_EAU),
    ]:
        fig.add_trace(go.Bar(
            x=annees, y=[getattr(a.structure, cle) for a in diag.analyses], name=nom,
            marker=dict(color=couleur, cornerradius=4, line=dict(color="#ffffff", width=2)),
            hovertemplate=f"{nom} : %{{y:,.0f}} €<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text="Fonds de roulement, BFR et trésorerie", font=dict(color=ENCRE, size=15)),
        barmode="group", hovermode="x unified",
    )
    return styliser(fig, hauteur=380, suffixe_y=" €")


def graphique_cascade(a: AnalyseExercice) -> go.Figure:
    s = a.sig
    etapes = [
        ("Chiffre d'affaires", "absolute", s.chiffre_affaires),
        ("Achats et charges externes", "relative", s.valeur_ajoutee - s.chiffre_affaires),
        ("Valeur ajoutée", "total", s.valeur_ajoutee),
        ("Personnel, impôts et taxes", "relative", s.excedent_brut_exploitation - s.valeur_ajoutee),
        ("EBE", "total", s.excedent_brut_exploitation),
        ("Amortissements et autres", "relative", s.resultat_exploitation - s.excedent_brut_exploitation),
        ("Résultat d'exploitation", "total", s.resultat_exploitation),
        ("Financier", "relative", s.resultat_financier),
        ("Exceptionnel", "relative", s.resultat_exceptionnel),
        ("Impôt et participation", "relative",
         s.resultat_net - s.resultat_courant_avant_impot - s.resultat_exceptionnel),
        ("Résultat net", "total", s.resultat_net),
    ]
    fig = go.Figure(go.Waterfall(
        x=[e[0] for e in etapes],
        measure=[e[1] for e in etapes],
        y=[e[2] if e[1] != "total" else 0 for e in etapes],
        connector=dict(line=dict(color=AXE, width=1)),
        increasing=dict(marker=dict(color=VERT_EAU)),
        decreasing=dict(marker=dict(color=ROUGE)),
        totals=dict(marker=dict(color=BLEU)),
        hovertemplate="%{x} : %{y:,.0f} €<extra></extra>",
        textposition="none",
    ))
    fig.update_layout(
        title=dict(text=f"Du chiffre d'affaires au résultat net ({a.annee})", font=dict(color=ENCRE, size=15)),
        showlegend=False,
    )
    fig = styliser(fig, hauteur=420, suffixe_y=" €")
    fig.update_xaxes(tickangle=-30)
    return fig


def graphique_score(diag: Diagnostic) -> go.Figure:
    annees = [str(a.annee) for a in diag.analyses]
    fig = go.Figure(go.Scatter(
        x=annees, y=[a.score.total for a in diag.analyses], mode="lines+markers+text",
        line=dict(color=BLEU, width=2), marker=dict(size=9, color=BLEU, line=dict(color="#ffffff", width=2)),
        text=[a.score.note for a in diag.analyses], textposition="top center",
        textfont=dict(color=ENCRE, size=13),
        hovertemplate="%{x} : %{y:.0f}/100<extra></extra>",
    ))
    fig.update_layout(title=dict(text="Évolution du score", font=dict(color=ENCRE, size=15)), showlegend=False)
    fig = styliser(fig, hauteur=300)
    fig.update_yaxes(range=[0, 105])
    return fig


# --- Tableaux --------------------------------------------------------------

def tableau_formate(diag: Diagnostic, groupes: list[str]) -> pd.DataFrame:
    brut = diag.tableau()
    lignes = []
    for cle, ind in INDICATEURS.items():
        if ind.groupe in groupes and cle in brut.index:
            ligne = {"Indicateur": ind.libelle}
            for annee in brut.columns:
                valeur = brut.loc[cle, annee]
                ligne[str(annee)] = formater(None if pd.isna(valeur) else float(valeur), ind.format)
            ligne["Définition"] = ind.aide
            lignes.append(ligne)
    return pd.DataFrame(lignes)


def comptes_bruts(entreprise: Entreprise, partie: str) -> pd.DataFrame:
    colonnes = {}
    for ex in entreprise.exercices:
        source = ex.compte_de_resultat if partie == "cr" else ex.bilan
        colonnes[str(ex.annee)] = {
            k.replace("_", " ").capitalize(): formater(v, "euros") for k, v in asdict(source).items()
        }
    return pd.DataFrame(colonnes)


# --- Barre latérale --------------------------------------------------------

with st.sidebar:
    st.markdown("## Lugdunum")
    st.caption("Diagnostic financier automatisé des PME françaises")

    source = st.radio("Source des données", ["Exemples", "Importer un fichier"], horizontal=True)
    entreprise: Entreprise | None = None
    if source == "Exemples":
        exemples = exemples_disponibles()
        choix = st.selectbox("Entreprise", list(exemples))
        entreprise = Entreprise.depuis_json(exemples[choix])
        st.caption("Les exemples sont des entreprises **fictives**, construites pour illustrer trois profils types.")
    else:
        fichier = st.file_uploader("Comptes annuels (JSON)", type="json")
        st.download_button(
            "Télécharger un modèle vierge", modele_vierge(), "modele_lugdunum.json",
            mime="application/json", icon=":material/download:",
        )
        if fichier is not None:
            try:
                entreprise = Entreprise.depuis_dict(json.load(fichier))
            except (ValueError, TypeError, json.JSONDecodeError) as erreur:
                st.error(f"Fichier illisible : {erreur}", icon=":material/error:")

    st.divider()
    st.caption(
        "Les comptes annuels publics, récupérés à partir du SIREN, arriveront dans une "
        "prochaine version. [Code source sur GitHub](https://github.com/jb4md58s2n-hue/Lugdunum)"
    )

if entreprise is None or not entreprise.exercices:
    st.title("Lugdunum")
    st.info("Importe un fichier de comptes annuels, ou choisis un exemple dans le menu.", icon=":material/info:")
    st.stop()

diag = diagnostiquer(entreprise)


# --- En-tête ---------------------------------------------------------------

etiquette = '<span class="etiquette-fictive">Entreprise fictive</span>' if entreprise.fictive else ""
st.markdown(f"# {entreprise.denomination} {etiquette}", unsafe_allow_html=True)
details = " · ".join(
    x for x in [
        f"SIREN {entreprise.siren}" if entreprise.siren else "",
        f"NAF {entreprise.code_naf} {entreprise.libelle_naf or ''}".strip() if entreprise.code_naf else "",
        f"{len(diag.analyses)} exercice(s) analysé(s)",
    ] if x
)
st.markdown(f'<p class="sous-titre">{details}</p>', unsafe_allow_html=True)

annees = [a.annee for a in diag.analyses]
if len(annees) > 1:
    annee = st.segmented_control("Exercice", annees, default=annees[-1], format_func=str) or annees[-1]
else:
    annee = annees[0]
a = next(x for x in diag.analyses if x.annee == annee)
index = annees.index(annee)
precedent = diag.analyses[index - 1] if index > 0 and annees[index - 1] == annee - 1 else None


# --- Score -----------------------------------------------------------------

col_score, col_axes = st.columns([1, 2], gap="medium")
couleur, statut = STATUTS[a.score.note]
texte_lettre = ENCRE if a.score.note == "C" else "#ffffff"
with col_score:
    st.markdown(
        f"""
        <div class="carte">
          <div style="color:{ENCRE_2}; font-size:.92rem;">Score Lugdunum {a.annee}</div>
          <div class="score-ligne"><span class="score-valeur">{a.score.total:.0f}</span>
               <span class="score-sur">/ 100</span></div>
          <div class="pastille"><span class="lettre" style="background:{couleur}; color:{texte_lettre};">
               {a.score.note}</span> {statut}</div>
          <div class="appreciation">{a.score.appreciation}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_axes:
    axes = [
        ("Rentabilité", a.score.rentabilite, "Marge d'EBE et marge nette"),
        ("Solvabilité", a.score.solvabilite, "Autonomie financière et capacité de remboursement"),
        ("Liquidité", a.score.liquidite, "Liquidité générale et trésorerie"),
        ("Activité", a.score.activite, "Croissance et délai clients"),
    ]
    html = "".join(
        f"""<div class="axe"><div class="axe-entete"><span>{nom} <span style="color:{ENCRE_MUETTE}">· {aide}</span></span>
            <b>{f"{valeur:.1f}".replace(".", ",")}/25</b></div><div class="jauge"><div style="width:{valeur / 25:.0%}"></div></div></div>"""
        for nom, valeur, aide in axes
    )
    st.markdown(f'<div class="carte">{html}</div>', unsafe_allow_html=True)

st.write("")


# --- Indicateurs clés ------------------------------------------------------

def variation(cle: str, groupe: str) -> str | None:
    if precedent is None:
        return None
    ecart = getattr(getattr(a, groupe), cle) - getattr(getattr(precedent, groupe), cle)
    # Signe ASCII : Streamlit s'en sert pour choisir la couleur et le sens de la flèche
    return formater(ecart, "euros") if ecart < 0 else "+" + formater(ecart, "euros")


k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Chiffre d'affaires", formater(a.sig.chiffre_affaires, "euros"),
    None if a.croissance_ca is None else f"{a.croissance_ca:+.1%}".replace(".", ","),
    border=True,
)
k2.metric("EBE", formater(a.sig.excedent_brut_exploitation, "euros"),
          variation("excedent_brut_exploitation", "sig"), border=True,
          help=f"Marge d'EBE : {formater(a.ratios.taux_marge_ebe, 'pct')}")
k3.metric("Résultat net", formater(a.sig.resultat_net, "euros"),
          variation("resultat_net", "sig"), border=True,
          help=f"Marge nette : {formater(a.ratios.taux_marge_nette, 'pct')}")
k4.metric("Trésorerie nette", formater(a.structure.tresorerie_nette, "euros"),
          variation("tresorerie_nette", "structure"), border=True,
          help="Disponibilités − découverts bancaires")


# --- Alertes ---------------------------------------------------------------

st.subheader("Points d'attention")
if not a.alertes:
    st.success("Aucune alerte sur cet exercice.", icon=":material/check_circle:")
for alerte in a.alertes:
    if alerte.niveau is Niveau.CRITIQUE:
        st.error(f"**Critique** · {alerte.message}", icon=":material/error:")
    elif alerte.niveau is Niveau.ATTENTION:
        st.warning(f"**Attention** · {alerte.message}", icon=":material/warning:")
    else:
        st.info(f"**Information** · {alerte.message}", icon=":material/info:")


# --- Analyse détaillée -----------------------------------------------------

st.subheader("Analyse détaillée")
onglet_evol, onglet_cascade, onglet_ratios, onglet_bilan, onglet_donnees = st.tabs(
    ["Évolution", "Cascade des SIG", "Ratios", "Bilan fonctionnel", "Comptes annuels"]
)

with onglet_evol:
    g1, g2 = st.columns(2)
    g1.plotly_chart(graphique_chiffre_affaires(diag), use_container_width=True)
    g2.plotly_chart(graphique_marges(diag), use_container_width=True)
    if len(diag.analyses) > 1:
        st.plotly_chart(graphique_score(diag), use_container_width=True)

with onglet_cascade:
    st.plotly_chart(graphique_cascade(a), use_container_width=True)
    st.dataframe(tableau_formate(diag, ["SIG"]), hide_index=True, use_container_width=True)

with onglet_ratios:
    for groupe in ["Rentabilité", "Solvabilité", "Liquidité", "Cycle d'exploitation"]:
        st.markdown(f"**{groupe}**")
        st.dataframe(tableau_formate(diag, [groupe]), hide_index=True, use_container_width=True)

with onglet_bilan:
    st.plotly_chart(graphique_structure(diag), use_container_width=True)
    st.caption("Trésorerie nette = fonds de roulement − BFR. Quand le BFR dépasse le fonds de roulement, "
               "l'entreprise finance son exploitation à découvert.")
    st.dataframe(tableau_formate(diag, ["Bilan fonctionnel"]), hide_index=True, use_container_width=True)

with onglet_donnees:
    c1, c2 = st.columns(2)
    c1.markdown("**Compte de résultat**")
    c1.dataframe(comptes_bruts(entreprise, "cr"), use_container_width=True, height=600)
    c2.markdown("**Bilan**")
    c2.dataframe(comptes_bruts(entreprise, "bilan"), use_container_width=True, height=600)


# --- Export ----------------------------------------------------------------

st.divider()
st.download_button(
    "Télécharger le diagnostic (Excel)",
    vers_excel(diag),
    f"diagnostic_{entreprise.denomination.lower().replace(' ', '_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    icon=":material/table_view:",
    type="primary",
)
st.caption("Lugdunum est un outil d'aide à l'analyse. Il ne remplace ni l'examen des annexes, "
           "ni le jugement d'un professionnel du chiffre.")
