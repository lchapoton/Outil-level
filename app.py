import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Investment Scoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f8f8f6; }
    .stApp { background-color: #f8f8f6; }

    /* Score badge */
    .score-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 999px;
        font-size: 15px;
        font-weight: 600;
        letter-spacing: .02em;
    }
    /* Verdict box */
    .verdict-box {
        padding: 18px 22px;
        border-radius: 12px;
        border-left: 4px solid;
        margin: 16px 0;
        line-height: 1.6;
    }
    /* Phase pill */
    .phase-pill {
        display: inline-block;
        padding: 5px 14px;
        border-radius: 8px;
        font-size: 13px;
        margin: 4px 4px 4px 0;
        font-weight: 500;
    }
    /* Flag item */
    .flag-item {
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 6px;
        font-size: 14px;
        background: #fff;
        border: 0.5px solid #e0e0dc;
    }
    /* Metric override */
    div[data-testid="metric-container"] {
        background: #fff;
        border: 0.5px solid #e0e0dc;
        border-radius: 10px;
        padding: 14px 18px;
    }
    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA & HELPERS
# ─────────────────────────────────────────────
KPI_DEF = [
    {"id": "bilan",      "label": "Santé bilan (cash / dette)",    "weight": 20, "hint": "Net cash positif → faible risque"},
    {"id": "earnings",   "label": "Visibilité des earnings",        "weight": 15, "hint": "Récurrence, prévisibilité des revenus"},
    {"id": "position",   "label": "Position concurrentielle",       "weight": 15, "hint": "Leader / challenger / niche"},
    {"id": "management", "label": "Qualité du management",          "weight": 15, "hint": "Track record, alignement, gouvernance"},
    {"id": "marche",     "label": "Dynamique de marché",            "weight": 10, "hint": "Croissance, régulation, disruption"},
    {"id": "multiples",  "label": "Niveau de valorisation",         "weight": 10, "hint": "Multiples vs comparables (inversé)"},
    {"id": "esg",        "label": "Controverses / ESG",             "weight": 8,  "hint": "Risques réputationnels ou légaux"},
    {"id": "liquidity",  "label": "Liquidité du titre",             "weight": 7,  "hint": "Free float, volumes, concentration"},
]

PRESETS = {
    "🟢  Leader de marché (cash)": {
        "company": "TechLeader SA", "sector": "Tech · Large Cap",
        "vals": {"bilan": 95, "earnings": 88, "position": 90, "management": 85,
                 "marche": 80, "multiples": 40, "esg": 85, "liquidity": 90}
    },
    "🟡  Croissance, dette modérée": {
        "company": "Acme Corp", "sector": "SaaS B2B · Série B",
        "vals": {"bilan": 55, "earnings": 60, "position": 65, "management": 70,
                 "marche": 75, "multiples": 55, "esg": 70, "liquidity": 50}
    },
    "🔴  Situation complexe / retournement": {
        "company": "Restructo Intl", "sector": "Industriel · Retournement",
        "vals": {"bilan": 20, "earnings": 25, "position": 30, "management": 35,
                 "marche": 40, "multiples": 75, "esg": 30, "liquidity": 35}
    },
}

def compute_score(vals):
    total_w = sum(k["weight"] for k in KPI_DEF)
    score = sum((vals[k["id"]] / 100) * k["weight"] for k in KPI_DEF)
    return round((score / total_w) * 100)

def score_color(s):
    if s >= 70: return "#639922"
    if s >= 45: return "#EF9F27"
    return "#E24B4A"

def score_label(s):
    if s >= 70: return "Faible complexité"
    if s >= 45: return "Complexité modérée"
    return "Haute complexité"

def risk_label(s):
    if s >= 70: return ("🟢 Faible", "Marge d'erreur confortable")
    if s >= 45: return ("⚠️ Moyen", "Marges d'erreur limitées")
    return ("🔴 Élevé", "Pas le droit à l'erreur")

def budget_info(s):
    if s >= 70:
        return "15–20 j", "Analyse standard", [
            ("Screening", "2–3j", "#EAF3DE", "#3B6D11"),
            ("Due dil. financière", "5–7j", "#EAF3DE", "#3B6D11"),
            ("Décision comité", "3–5j", "#EAF3DE", "#3B6D11"),
        ]
    if s >= 45:
        return "30–50 j", "Analyse approfondie", [
            ("Screening étendu", "5–7j", "#FAEEDA", "#7A4A0A"),
            ("Due dil. financière", "10–15j", "#FAEEDA", "#7A4A0A"),
            ("Experts sectoriels", "7–10j", "#FAEEDA", "#7A4A0A"),
            ("Comité + négociation", "8–12j", "#FAEEDA", "#7A4A0A"),
        ]
    return "60–90 j", "Analyse de retournement", [
        ("Audit complet", "15–20j", "#FCEBEB", "#7A1F1F"),
        ("Expert management", "10–15j", "#FCEBEB", "#7A1F1F"),
        ("Restructuration", "15–20j", "#FCEBEB", "#7A1F1F"),
        ("Legal & closing", "15–20j", "#FCEBEB", "#7A1F1F"),
    ]

def verdict_info(s):
    if s >= 70:
        return "#EAF3DE", "#3B6D11", "🏆 Dossier très lisible — faible complexité", \
               "Situation claire : position de marché forte, bilan sain, earnings visibles. L'équipe dispose d'une bonne marge d'erreur. Budget temps resserré possible."
    if s >= 45:
        return "#FDF3E7", "#8A5C00", "💼 Dossier lisible mais exigeant", \
               "Complexité modérée. Certains axes nécessitent une attention particulière. Marge d'erreur réduite — prévoir une due diligence renforcée avant décision."
    return "#FCEBEB", "#7A1F1F", "⚠️ Dossier complexe — pas le droit à l'erreur", \
           "Situation difficile. Multiples facteurs de risque identifiés. Mobilisation maximale de l'équipe requise. Chaque hypothèse doit être validée indépendamment."

def get_flags(vals):
    flags = []
    if vals["bilan"] < 40:
        flags.append(("🔴", "Bilan sous pression : endettement élevé ou cash insuffisant — risque de refinancement"))
    if vals["management"] < 45:
        flags.append(("🔴", "Management : track record incertain ou gouvernance fragile — due diligence humaine obligatoire"))
    if vals["earnings"] < 40:
        flags.append(("🟡", "Visibilité earnings faible : modélisation difficile, multiplier les scénarios"))
    if vals["position"] < 40:
        flags.append(("🟡", "Position concurrentielle faible : risque de disruption ou pression sur les marges"))
    if vals["esg"] < 40:
        flags.append(("🟡", "Controverses ESG identifiées : risque réputationnel ou régulateur à analyser"))
    if vals["multiples"] > 70:
        flags.append(("🟠", "Valorisation élevée vs comparables : upside limité, thèse d'investissement à solidifier"))
    if vals["liquidity"] < 35:
        flags.append(("🔵", "Liquidité limitée : contrainte de sortie à intégrer dans la structuration"))
    if not flags:
        flags.append(("✅", "Aucun point critique identifié — dossier dans les paramètres normaux"))
    return flags

def make_radar(vals):
    labels = [k["label"] for k in KPI_DEF]
    values = [vals[k["id"]] for k in KPI_DEF]
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed, theta=labels_closed,
        fill='toself',
        fillcolor='rgba(55, 138, 221, 0.12)',
        line=dict(color='#378ADD', width=2),
        marker=dict(size=5, color='#378ADD'),
        name='Score',
        hovertemplate='%{theta}<br>Score : %{r}<extra></extra>'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10),
                            gridcolor='rgba(0,0,0,0.08)'),
            angularaxis=dict(tickfont=dict(size=11)),
            bgcolor='rgba(0,0,0,0)',
        ),
        showlegend=False,
        margin=dict(t=30, b=30, l=60, r=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=360,
    )
    return fig

def make_bar_chart(vals):
    df = pd.DataFrame([
        {"KPI": k["label"], "Score": vals[k["id"]], "Poids": k["weight"]}
        for k in KPI_DEF
    ]).sort_values("Score")

    colors = [score_color(v) for v in df["Score"]]
    fig = go.Figure(go.Bar(
        x=df["Score"], y=df["KPI"],
        orientation='h',
        marker_color=colors,
        text=[f'{v}/100' for v in df["Score"]],
        textposition='outside',
        hovertemplate='%{y}<br>Score : %{x}<extra></extra>'
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 110], showgrid=True, gridcolor='rgba(0,0,0,0.06)'),
        yaxis=dict(tickfont=dict(size=12)),
        margin=dict(t=10, b=10, l=10, r=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=320,
    )
    return fig


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Paramètres du dossier")
    st.markdown("---")

    preset_choice = st.selectbox("Charger un exemple", list(PRESETS.keys()))
    preset = PRESETS[preset_choice]

    company_name = st.text_input("Nom de la société", value=preset["company"])
    sector = st.text_input("Secteur / stade", value=preset["sector"])
    analyst = st.text_input("Analyste", value="")
    analysis_date = st.date_input("Date d'analyse", value=date.today())

    st.markdown("---")
    st.markdown("### 📊 Scores KPI (0–100)")
    st.caption("0 = très défavorable · 100 = excellent")

    vals = {}
    for k in KPI_DEF:
        default = preset["vals"][k["id"]]
        vals[k["id"]] = st.slider(
            f"{k['label']}",
            min_value=0, max_value=100,
            value=default,
            help=k["hint"],
            key=f"kpi_{k['id']}"
        )

    st.markdown("---")
    st.caption("💡 Adapte les poids directement dans `app.py` → `KPI_DEF`")


# ─────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────
score = compute_score(vals)
color = score_color(score)
label = score_label(score)
risk_lbl, risk_sub = risk_label(score)
budget_j, budget_sub, phases = budget_info(score)
bg_v, bc_v, title_v, msg_v = verdict_info(score)
flags = get_flags(vals)

# Header
col_title, col_meta = st.columns([3, 1])
with col_title:
    st.markdown(f"## 📊 {company_name}")
    st.caption(f"{sector}" + (f" · {analyst}" if analyst else "") + f" · {analysis_date.strftime('%d/%m/%Y')}")
with col_meta:
    st.markdown(
        f"<div style='text-align:right'>"
        f"<span class='score-badge' style='background:{color}22;color:{color};border:1px solid {color}44'>"
        f"Score {score}/100 — {label}</span></div>",
        unsafe_allow_html=True
    )

# Verdict
st.markdown(
    f"<div class='verdict-box' style='background:{bg_v};border-color:{bc_v};color:{bc_v}'>"
    f"<strong>{title_v}</strong><br>{msg_v}"
    f"</div>", unsafe_allow_html=True
)

# ── Métriques ──────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Score global", f"{score} / 100", label)
with m2:
    st.metric("Budget temps", budget_j, budget_sub)
with m3:
    st.metric("Niveau de risque", risk_lbl, risk_sub)
with m4:
    top_kpi = max(KPI_DEF, key=lambda k: vals[k["id"]])
    worst_kpi = min(KPI_DEF, key=lambda k: vals[k["id"]])
    st.metric("Point fort / faible", f"↑ {vals[top_kpi['id']]}", f"↓ {worst_kpi['label'][:18]}… {vals[worst_kpi['id']]}")

st.markdown("---")

# ── Charts ─────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📡 Vue radar", "📊 Vue barres"])
with tab1:
    st.plotly_chart(make_radar(vals), use_container_width=True)
with tab2:
    st.plotly_chart(make_bar_chart(vals), use_container_width=True)

st.markdown("---")

# ── Budget temps ───────────────────────────────────────────────────────────
st.markdown("### 📅 Budget temps recommandé")
cols = st.columns(len(phases))
for i, (phase_label, phase_time, phase_bg, phase_tc) in enumerate(phases):
    with cols[i]:
        st.markdown(
            f"<div class='phase-pill' style='background:{phase_bg};color:{phase_tc};display:block;text-align:center'>"
            f"<div style='font-weight:600'>{phase_label}</div>"
            f"<div style='font-size:12px;opacity:.75'>{phase_time}</div></div>",
            unsafe_allow_html=True
        )

st.markdown("---")

# ── KPI détail ─────────────────────────────────────────────────────────────
st.markdown("### 🔍 Détail par axe")
kpi_cols = st.columns(4)
for i, k in enumerate(KPI_DEF):
    v = vals[k["id"]]
    c = score_color(v)
    with kpi_cols[i % 4]:
        st.markdown(
            f"<div style='background:#fff;border:0.5px solid #e0e0dc;border-radius:10px;padding:12px 14px;margin-bottom:10px'>"
            f"<div style='font-size:12px;color:#888;margin-bottom:4px'>{k['label']}</div>"
            f"<div style='font-size:22px;font-weight:600;color:{c}'>{v}<span style='font-size:13px;color:#aaa'>/100</span></div>"
            f"<div style='height:6px;background:#f0f0ec;border-radius:3px;margin:6px 0'>"
            f"<div style='width:{v}%;height:100%;background:{c};border-radius:3px'></div></div>"
            f"<div style='font-size:11px;color:#aaa'>Poids {k['weight']}% · {k['hint']}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

st.markdown("---")

# ── Points d'attention ─────────────────────────────────────────────────────
st.markdown("### 🚩 Points d'attention")
for icon, text in flags:
    st.markdown(f"<div class='flag-item'>{icon} {text}</div>", unsafe_allow_html=True)

st.markdown("---")

# ── Message équipe ──────────────────────────────────────────────────────────
st.markdown("### 💬 Message équipe (à copier)")
worst = min(KPI_DEF, key=lambda k: vals[k["id"]])
best = max(KPI_DEF, key=lambda k: vals[k["id"]])

msg_team = f"""📊 *Dossier : {company_name}* — {analysis_date.strftime('%d/%m/%Y')}
Analyste : {analyst if analyst else 'N/A'} · Secteur : {sector}

*Score de complexité : {score}/100 — {label}*
Niveau de risque : {risk_lbl}
Budget temps recommandé : {budget_j}

Point fort identifié : {best['label']} ({vals[best['id']]}/100)
Point de vigilance : {worst['label']} ({vals[worst['id']]}/100)

Verdict : {title_v}
{msg_v}

→ Prochaine étape : {phases[0][0]} ({phases[0][1]})"""

st.code(msg_team, language=None)

st.caption("Copie ce message et colle-le dans Slack / Teams / email.")
