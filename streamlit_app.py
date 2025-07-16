# app.py

import streamlit as st

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import datetime

# Chargement des données
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("all_gardens.xlsx")
        return df
    except FileNotFoundError:
        st.warning("Le fichier 'all_gardens.xlsx' est introuvable.")
        return pd.DataFrame()

# Titre principal
st.set_page_config(page_title="Suivi des Bénéficiaires | Gardening", layout="wide")
st.title("🌿 Suivi des Bénéficiaires du Programme Gardening")
st.markdown("**Application interactive basée sur le fichier Quarto `tracking-gardening.qmd`**")

# Chargement des données
df = load_data()

if df.empty:
    st.stop()

# Filtres
with st.sidebar:
    st.header("🎯 Filtres")
    office_filter = st.multiselect("Choisir les offices :", sorted(df['office'].dropna().unique()), default=None)
    date_col = 'start_date'

    # ✅ Conversion explicite
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # ✅ Gestion sécurisée de NaT
    min_date_raw = df[date_col].dropna().min()
    max_date_raw = df[date_col].dropna().max()

    if pd.isna(min_date_raw) or pd.isna(max_date_raw):
        st.warning("La colonne de date ne contient pas de valeurs valides.")
        st.stop()

    min_date = min_date_raw.date()
    max_date = max_date_raw.date()

    date_range = st.date_input("Période (début / fin)", [min_date, max_date])




# Filtrage des données
if office_filter:
    df = df[df['office'].isin(office_filter)]

if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range)
    df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]

# Affichage des données filtrées
st.subheader("📊 Données Filtrées")
st.dataframe(df.head(100))

# Statistiques
st.subheader("🔍 Statistiques")
col1, col2, col3 = st.columns(3)
col1.metric("Bénéficiaires totaux", len(df))
col2.metric("Âge moyen", f"{df['age'].mean():.1f} ans")
col3.metric("Cycle 4 démarré", df[date_col].notna().sum())

# Histogramme par département
st.subheader("📍 Répartition par département")
fig1 = px.histogram(df, x='departement', color='departement')
st.plotly_chart(fig1, use_container_width=True)

# Courbe par date de début cycle 4
st.subheader("📆 Évolution dans le temps")
if date_col in df.columns:
    fig2 = px.histogram(df, x=date_col, nbins=30, title="Cycle 4 start - par date")
    st.plotly_chart(fig2, use_container_width=True)

# Carte (si coordonnées disponibles)
if 'latitude' in df.columns and 'longitude' in df.columns:
    st.subheader("🗺️ Carte des bénéficiaires")
    st.map(df[['latitude', 'longitude']])

from io import BytesIO

# 📥 Téléchargement des données filtrées
st.subheader("⬇️ Télécharger les données filtrées")
buffer = BytesIO()
df.to_excel(buffer, index=False, engine='openpyxl')
buffer.seek(0)

st.download_button(
    label="📥 Télécharger en Excel",
    data=buffer,
    file_name="donnees_filtrees.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)