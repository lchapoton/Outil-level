import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date
import sqlite3
import os

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Investment Scoring",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { background-color: #f8f8f6; }
    .stApp { background-color: #f8f8f6; }
    .score-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 999px;
        font-size: 15px;
        font-weight: 600;
    }
    .verdict-box {
        padding: 18px 22px;
        border-radius: 12px;
        border-left: 4px solid;
        margin: 16px 0;
        line-height: 1.6;
    }
    .flag-item {
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 6px;
        font-size: 14px;
        background: #fff;
        border: 0.5px solid #e0e0dc;
    }
    .kpi-card {
        background: #fff;
        border: 0.5px solid #e0e0dc;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
    }
    div[data-testid="metric-container"] {
        background: #fff;
        border: 0.5px solid #e0e0dc;
        border-radius: 10px;
        padding: 14px 18px;
    }
    #MainMenu, footer { visibility: hidden; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# KPI DEFINITION
# ─────────────────────────────────────────────
KPI_DEF = [
    {"id": "earnings",    "label": "Stabilité des earnings",      "weight": 18, "hint": "Volatilité historique des résultats, récurrence des revenus"},
    {"id": "bilan",       "label": "Structure de bilan",          "weight": 16, "hint": "Dette nette/EBITDA, maturités, génération de FCF"},
    {"id": "position",    "label": "Position concurrentielle",    "weight": 16, "hint": "Leader/challenger, pricing power, barrières à l'entrée"},
    {"id": "comptable",   "label": "Clarté comptable",            "weight": 14, "hint": "Retraitements, gap reported/adjusted, hors-bilan"},
    {"id": "management",  "label": "Qualité du management",       "weight": 14, "hint": "Track record, guidance tenue, alignement actionnaire"},
    {"id": "visibilite",  "label": "Visibilité à 3 ans",          "weight": 12, "hint": "Backlog, récurrence revenus, dispersion consensus"},
    {"id": "controverses","label": "Controverses & risques",      "weight": 10, "hint": "Litiges, régulation, risques ESG actifs"},
    {"id": "valorisation","label": "Complexité de valorisation",  "weight": 10, "hint": "Multiples vs historique, comparables, valeur terminale"},
]

FONDS = ["Fonds Tech", "Fonds Value", "Fonds Europe", "Fonds Émergents", "Autre"]

# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
DB_PATH = "scoring.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dossiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            societe TEXT NOT NULL,
            secteur TEXT,
            fonds TEXT,
            date_analyse TEXT,
            score INTEGER,
            label TEXT,
            earnings INTEGER, bilan INTEGER, position INTEGER,
            comptable INTEGER, management INTEGER, visibilite INTEGER,
            controverses INTEGER, valorisation INTEGER,
            verdict TEXT,
            budget TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_dossier(data):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO dossiers
        (societe, secteur, fonds, date_analyse, score, label,
         earnings, bilan, position, comptable, management, visibilite,
         controverses, valorisation, verdict, budget)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, data)
    conn.commit()
    conn.close()

@st.cache_data(ttl=5)
def load_dossiers():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM dossiers ORDER BY created_at DESC", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

def delete_dossier(dossier_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM dossiers WHERE id = ?", (dossier_id,))
    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────
# SCORING LOGIC
# ─────────────────────────────────────────────
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
           "Situation difficile. Multiples facteurs de risque identifiés. Mobilisation maximale requise. Chaque hypothèse doit être validée indépendamment."

def get_flags(vals):
    flags = []
    if vals["bilan"] < 40:
        flags.append(("🔴", "Bilan sous pression : endettement élevé — risque de refinancement"))
    if vals["management"] < 45:
        flags.append(("🔴", "Management : track record incertain — due diligence humaine obligatoire"))
    if vals["earnings"] < 40:
        flags.append(("🟡", "Stabilité earnings faible : modélisation difficile, multiplier les scénarios"))
    if vals["position"] < 40:
        flags.append(("🟡", "Position concurrentielle faible : risque de disruption ou pression sur les marges"))
    if vals["controverses"] < 40:
        flags.append(("🟡", "Controverses identifiées : risque réputationnel ou régulateur à analyser"))
    if vals["valorisation"] < 40:
        flags.append(("🟠", "Valorisation complexe : peu de comparables ou multiples très élevés"))
    if vals["visibilite"] < 35:
        flags.append(("🔵", "Visibilité 3 ans très faible : thèse d'investissement fragile"))
    if vals["comptable"] < 40:
        flags.append(("🟡", "Clarté comptable faible : retraitements importants, risque de modélisation"))
    if not flags:
        flags.append(("✅", "Aucun point critique identifié — dossier dans les paramètres normaux"))
    return flags

# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
def make_radar(vals):
    labels = [k["label"] for k in KPI_DEF]
    values = [vals[k["id"]] for k in KPI_DEF]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=labels + [labels[0]],
        fill='toself',
        fillcolor='rgba(55,138,221,0.12)',
        line=dict(color='#378ADD', width=2),
        marker=dict(size=5, color='#378ADD'),
        hovertemplate='%{theta}<br>Score : %{r}<extra></extra>'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10), gridcolor='rgba(0,0,0,0.08)'),
            angularaxis=dict(tickfont=dict(size=11)),
            bgcolor='rgba(0,0,0,0)',
        ),
        showlegend=False,
        margin=dict(t=30, b=30, l=60, r=60),
        paper_bgcolor='rgba(0,0,0,0)',
        height=360,
    )
    return fig

def make_bar(vals):
    df = pd.DataFrame([
        {"KPI": k["label"], "Score": vals[k["id"]]}
        for k in KPI_DEF
    ]).sort_values("Score")
    fig = go.Figure(go.Bar(
        x=df["Score"], y=df["KPI"],
        orientation='h',
        marker_color=[score_color(v) for v in df["Score"]],
        text=[f'{v}/100' for v in df["Score"]],
        textposition='outside',
        hovertemplate='%{y}<br>Score : %{x}<extra></extra>'
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 115], showgrid=True, gridcolor='rgba(0,0,0,0.06)'),
        yaxis=dict(tickfont=dict(size=11)),
        margin=dict(t=10, b=10, l=10, r=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
    )
    return fig

def make_portfolio_bar(df):
    df_sorted = df.sort_values("score", ascending=True).tail(20)
    colors = [score_color(s) for s in df_sorted["score"]]
    fig = go.Figure(go.Bar(
        x=df_sorted["score"],
        y=df_sorted["societe"],
        orientation='h',
        marker_color=colors,
        text=[f'{s}/100' for s in df_sorted["score"]],
        textposition='outside',
        hovertemplate='%{y}<br>Score : %{x}<extra></extra>'
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 115], showgrid=True, gridcolor='rgba(0,0,0,0.06)'),
        yaxis=dict(tickfont=dict(size=11)),
        margin=dict(t=10, b=10, l=10, r=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=max(250, len(df_sorted) * 32),
    )
    return fig

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["📋 Analyse dossier", "📊 Vue portefeuille"])

# ══════════════════════════════════════════════
# TAB 1 — ANALYSE DOSSIER
# ══════════════════════════════════════════════
with tab1:
    with st.sidebar:
        st.markdown("## 📋 Dossier")
        st.markdown("---")

        societe = st.text_input("Nom de la société", placeholder="Ex : Hermès, LVMH...")
        secteur = st.text_input("Secteur", placeholder="Ex : Luxe, SaaS B2B...")
        fonds_sel = st.selectbox("Fonds", FONDS)
        date_analyse = st.date_input("Date d'analyse", value=date.today())

        st.markdown("---")
        st.markdown("### 📊 Scores KPI (0–100)")
        st.caption("0 = très défavorable · 100 = excellent")

        vals = {}
        for k in KPI_DEF:
            vals[k["id"]] = st.slider(
                k["label"], min_value=0, max_value=100, value=50,
                help=k["hint"], key=f"sl_{k['id']}"
            )

        st.markdown("---")

        save_disabled = not societe.strip()
        if st.button("💾 Sauvegarder ce dossier", disabled=save_disabled, use_container_width=True):
            score = compute_score(vals)
            _, _, verdict_title, _ = verdict_info(score)
            budget_j, _, _ = budget_info(score)
            save_dossier((
                societe.strip(), secteur, fonds_sel,
                date_analyse.strftime('%d/%m/%Y'),
                score, score_label(score),
                vals["earnings"], vals["bilan"], vals["position"],
                vals["comptable"], vals["management"], vals["visibilite"],
                vals["controverses"], vals["valorisation"],
                verdict_title, budget_j
            ))
            st.cache_data.clear()
            st.success(f"✅ {societe} sauvegardé !")

        if save_disabled:
            st.caption("⬆️ Entre le nom de la société pour sauvegarder")

    # ── Main content ──
    score = compute_score(vals)
    color = score_color(score)
    label = score_label(score)
    risk_lbl, risk_sub = risk_label(score)
    budget_j, budget_sub, phases = budget_info(score)
    bg_v, bc_v, title_v, msg_v = verdict_info(score)
    flags = get_flags(vals)

    # Header
    col_title, col_badge = st.columns([3, 1])
    with col_title:
        name_display = societe if societe.strip() else "Nouveau dossier"
        st.markdown(f"## {name_display}")
        sub = []
        if secteur: sub.append(secteur)
        if fonds_sel: sub.append(fonds_sel)
        sub.append(date_analyse.strftime('%d/%m/%Y'))
        st.caption(" · ".join(sub))
    with col_badge:
        st.markdown(
            f"<div style='text-align:right;padding-top:12px'>"
            f"<span class='score-badge' style='background:{color}22;color:{color};border:1px solid {color}44'>"
            f"Score {score}/100</span></div>",
            unsafe_allow_html=True
        )

    # Verdict
    st.markdown(
        f"<div class='verdict-box' style='background:{bg_v};border-color:{bc_v};color:{bc_v}'>"
        f"<strong>{title_v}</strong><br>{msg_v}</div>",
        unsafe_allow_html=True
    )

    # Métriques
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Score global", f"{score} / 100", label)
    with m2:
        st.metric("Budget temps recommandé", budget_j, budget_sub)
    with m3:
        st.metric("Niveau de risque", risk_lbl, risk_sub)

    st.markdown("---")

    # Charts
    c1, c2 = st.tabs(["📡 Vue radar", "📊 Vue barres"])
    with c1:
        st.plotly_chart(make_radar(vals), use_container_width=True)
    with c2:
        st.plotly_chart(make_bar(vals), use_container_width=True)

    st.markdown("---")

    # Budget timeline
    st.markdown("### 📅 Allocation budgétaire recommandée")
    phase_cols = st.columns(len(phases))
    for i, (pl, pt, pbg, ptc) in enumerate(phases):
        with phase_cols[i]:
            st.markdown(
                f"<div style='background:{pbg};color:{ptc};border-radius:8px;padding:10px;text-align:center'>"
                f"<div style='font-weight:600;font-size:13px'>{pl}</div>"
                f"<div style='font-size:12px;opacity:.75'>{pt}</div></div>",
                unsafe_allow_html=True
            )

    st.markdown("---")

    # KPI détail + Flags côte à côte
    col_kpi, col_flags = st.columns([3, 2])

    with col_kpi:
        st.markdown("### 🔍 Détail par KPI")
        kpi_cols = st.columns(2)
        for i, k in enumerate(KPI_DEF):
            v = vals[k["id"]]
            c = score_color(v)
            with kpi_cols[i % 2]:
                st.markdown(
                    f"<div class='kpi-card'>"
                    f"<div style='font-size:12px;color:#888;margin-bottom:4px'>{k['label']}</div>"
                    f"<div style='font-size:22px;font-weight:600;color:{c}'>{v}"
                    f"<span style='font-size:12px;color:#aaa'>/100</span></div>"
                    f"<div style='height:5px;background:#f0f0ec;border-radius:3px;margin:5px 0'>"
                    f"<div style='width:{v}%;height:100%;background:{c};border-radius:3px'></div></div>"
                    f"<div style='font-size:11px;color:#aaa'>Poids {k['weight']}%</div></div>",
                    unsafe_allow_html=True
                )

    with col_flags:
        st.markdown("### 🚩 Points d'attention")
        for icon, text in flags:
            st.markdown(f"<div class='flag-item'>{icon} {text}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Message équipe
    st.markdown("### 💬 Message équipe")
    worst = min(KPI_DEF, key=lambda k: vals[k["id"]])
    best = max(KPI_DEF, key=lambda k: vals[k["id"]])
    msg_team = f"""📊 *Dossier : {name_display}* — {date_analyse.strftime('%d/%m/%Y')}
Fonds : {fonds_sel}{f" · Secteur : {secteur}" if secteur else ""}

*Score de complexité : {score}/100 — {label}*
Niveau de risque : {risk_lbl}
Budget temps recommandé : {budget_j}

Point fort : {best['label']} ({vals[best['id']]}/100)
Point de vigilance : {worst['label']} ({vals[worst['id']]}/100)

Verdict : {title_v}
{msg_v}

→ Prochaine étape : {phases[0][0]} ({phases[0][1]})"""
    st.code(msg_team, language=None)

# ══════════════════════════════════════════════
# TAB 2 — VUE PORTEFEUILLE
# ══════════════════════════════════════════════
with tab2:
    df = load_dossiers()

    if df.empty:
        st.info("Aucun dossier sauvegardé. Analyse un dossier dans l'onglet précédent et clique sur 'Sauvegarder'.")
    else:
        # Filtres
        f1, f2, f3 = st.columns(3)
        with f1:
            fonds_filter = st.selectbox("Filtrer par fonds", ["Tous"] + FONDS, key="pf_fonds")
        with f2:
            niveau_filter = st.selectbox("Filtrer par niveau", ["Tous", "🟢 Faible complexité", "🟡 Complexité modérée", "🔴 Haute complexité"], key="pf_niveau")
        with f3:
            sort_by = st.selectbox("Trier par", ["Date (récent)", "Score (croissant)", "Score (décroissant)"], key="pf_sort")

        df_f = df.copy()
        if fonds_filter != "Tous":
            df_f = df_f[df_f["fonds"] == fonds_filter]
        if niveau_filter != "Tous":
            label_map = {"🟢 Faible complexité": "Faible complexité", "🟡 Complexité modérée": "Complexité modérée", "🔴 Haute complexité": "Haute complexité"}
            df_f = df_f[df_f["label"] == label_map[niveau_filter]]
        if sort_by == "Score (croissant)":
            df_f = df_f.sort_values("score")
        elif sort_by == "Score (décroissant)":
            df_f = df_f.sort_values("score", ascending=False)

        st.markdown("---")

        # KPIs globaux
        n_green = len(df_f[df_f["score"] >= 70])
        n_amber = len(df_f[(df_f["score"] >= 45) & (df_f["score"] < 70)])
        n_red   = len(df_f[df_f["score"] < 45])

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Total dossiers", len(df_f))
        with k2:
            st.metric("🟢 Lisibles", n_green)
        with k3:
            st.metric("🟡 Modérés", n_amber)
        with k4:
            st.metric("🔴 Complexes", n_red)

        st.markdown("---")

        # Top 10 meilleurs / pires
        col_best, col_worst = st.columns(2)

        with col_best:
            st.markdown("#### 🏆 Top 10 — dossiers les plus lisibles")
            top10 = df_f.nlargest(10, "score")[["societe", "fonds", "score", "label", "budget", "date_analyse"]]
            for _, row in top10.iterrows():
                c = score_color(row["score"])
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:10px;padding:8px 10px;"
                    f"background:#fff;border:0.5px solid #e0e0dc;border-radius:8px;margin-bottom:6px'>"
                    f"<span style='font-size:16px;font-weight:600;color:{c};min-width:36px'>{row['score']}</span>"
                    f"<div style='flex:1'>"
                    f"<div style='font-size:13px;font-weight:500'>{row['societe']}</div>"
                    f"<div style='font-size:11px;color:#888'>{row['fonds']} · {row['date_analyse']}</div>"
                    f"</div>"
                    f"<span style='font-size:11px;color:{c};background:{c}22;padding:2px 8px;border-radius:99px'>{row['budget']}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

        with col_worst:
            st.markdown("#### ⚠️ Top 10 — dossiers les plus complexes")
            bot10 = df_f.nsmallest(10, "score")[["societe", "fonds", "score", "label", "budget", "date_analyse"]]
            for _, row in bot10.iterrows():
                c = score_color(row["score"])
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:10px;padding:8px 10px;"
                    f"background:#fff;border:0.5px solid #e0e0dc;border-radius:8px;margin-bottom:6px'>"
                    f"<span style='font-size:16px;font-weight:600;color:{c};min-width:36px'>{row['score']}</span>"
                    f"<div style='flex:1'>"
                    f"<div style='font-size:13px;font-weight:500'>{row['societe']}</div>"
                    f"<div style='font-size:11px;color:#888'>{row['fonds']} · {row['date_analyse']}</div>"
                    f"</div>"
                    f"<span style='font-size:11px;color:{c};background:{c}22;padding:2px 8px;border-radius:99px'>{row['budget']}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

        st.markdown("---")

        # Vue graphique
        if len(df_f) >= 2:
            st.markdown("#### 📊 Scores par société")
            st.plotly_chart(make_portfolio_bar(df_f), use_container_width=True)

        st.markdown("---")

        # KPI le plus faible en moyenne
        st.markdown("#### 🔍 KPI les plus faibles en moyenne (sur le portefeuille filtré)")
        kpi_means = {k["label"]: df_f[k["id"]].mean() for k in KPI_DEF if k["id"] in df_f.columns}
        if kpi_means:
            kpi_df = pd.DataFrame(list(kpi_means.items()), columns=["KPI", "Moyenne"]).sort_values("Moyenne")
            fig_kpi = go.Figure(go.Bar(
                x=kpi_df["Moyenne"].round(1), y=kpi_df["KPI"],
                orientation='h',
                marker_color=[score_color(v) for v in kpi_df["Moyenne"]],
                text=[f'{v:.0f}' for v in kpi_df["Moyenne"]],
                textposition='outside',
            ))
            fig_kpi.update_layout(
                xaxis=dict(range=[0, 115], showgrid=True, gridcolor='rgba(0,0,0,0.06)'),
                margin=dict(t=10, b=10, l=10, r=40),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=280,
            )
            st.plotly_chart(fig_kpi, use_container_width=True)

        st.markdown("---")

        # Tableau complet
        with st.expander("📄 Voir tous les dossiers"):
            cols_display = ["societe", "secteur", "fonds", "date_analyse", "score", "label", "budget"]
            cols_available = [c for c in cols_display if c in df_f.columns]
            st.dataframe(
                df_f[cols_available].rename(columns={
                    "societe": "Société", "secteur": "Secteur", "fonds": "Fonds",
                    "date_analyse": "Date", "score": "Score", "label": "Niveau", "budget": "Budget"
                }),
                use_container_width=True, hide_index=True
            )

            # Suppression
            st.markdown("**Supprimer un dossier**")
            del_col1, del_col2 = st.columns([3, 1])
            with del_col1:
                options = [f"{row['societe']} — {row['date_analyse']} (id:{row['id']})" for _, row in df_f.iterrows()]
                to_delete = st.selectbox("Choisir le dossier à supprimer", options, key="del_select")
            with del_col2:
                if st.button("🗑️ Supprimer", key="del_btn"):
                    dossier_id = int(to_delete.split("id:")[1].replace(")", ""))
                    delete_dossier(dossier_id)
                    st.cache_data.clear()
                    st.rerun()
