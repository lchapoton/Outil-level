# Investment Scoring Dashboard

Dashboard de scoring de dossiers d'investissement — Streamlit.

## Lancement local (première fois)

```bash
# 1. Installer les dépendances (une seule fois)
pip install -r requirements.txt

# 2. Lancer l'app
streamlit run app.py
```

L'app s'ouvre automatiquement dans le navigateur sur `http://localhost:8501`

---

## Déploiement gratuit (partageable à toute l'équipe)

### Option 1 — Streamlit Community Cloud (recommandé, gratuit)
1. Mettre le dossier sur un repo GitHub (privé ou public)
2. Aller sur https://share.streamlit.io
3. Connecter le repo → choisir `app.py` → Deploy
4. Tu obtiens un lien `https://xxx.streamlit.app` à partager à l'équipe

### Option 2 — Serveur interne
```bash
streamlit run app.py --server.port 8080 --server.address 0.0.0.0
```
Accessible sur `http://[IP-du-serveur]:8080`

---

## Personnaliser les KPI

Dans `app.py`, modifie la liste `KPI_DEF` :

```python
KPI_DEF = [
    {"id": "bilan",   "label": "Santé bilan",  "weight": 20, "hint": "..."},
    # Ajoute / modifie / supprime des lignes ici
    # La somme des weights n'a pas besoin de faire 100 (normalisé automatiquement)
]
```

## Ajouter tes propres presets sectoriels

Dans `app.py`, ajoute un entrée dans `PRESETS` :

```python
PRESETS["🏭 Industriel mature"] = {
    "company": "Exemple SA",
    "sector": "Industriel · Mid Cap",
    "vals": {"bilan": 70, "earnings": 65, ...}
}
```
