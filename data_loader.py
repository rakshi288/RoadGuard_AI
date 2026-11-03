"""
RoadGuard AI - Data Loading and Preprocessing Module
Loads the Karnataka accident dataset once and caches it for all pages.
"""

import pandas as pd
import numpy as np
import streamlit as st

DATASET_PATH = "templates/dataset/Copy of AccidentReports.csv"

VALID_SEVERITY = ["Damage Only", "Simple Injury", "Grievous Injury", "Fatal"]

SEVERITY_ORDER = ["Damage Only", "Simple Injury", "Grievous Injury", "Fatal"]

SEVERITY_COLORS = {
    "Damage Only": "#2ecc71",
    "Simple Injury": "#f39c12",
    "Grievous Injury": "#e67e22",
    "Fatal": "#e74c3c",
}

WEATHER_MAP = {
    "Clear": "Clear",
    "Fine": "Clear",
    "Cloudy": "Cloudy",
    "Light Rain": "Rainy",
    "Heavy Rain": "Rainy",
    "Fog / Mist": "Foggy",
    "Mist or Fog": "Foggy",
    "Very Hot": "Extreme Heat",
    "Very Cold": "Extreme Cold",
    "Snow": "Snow/Ice",
    "Wind": "Windy",
    "Strong Wind": "Windy",
    "Dust Storn": "Dust Storm",
    "Others": "Others",
    "Not Applicable": "Not Applicable",
    "Hail or Sleet": "Snow/Ice",
    "Flooding of Slipways/Rivulets": "Rainy",
}


@st.cache_data(show_spinner=False)
def load_data():
    """Load and clean the full dataset. Cached after first load."""
    df = pd.read_csv(DATASET_PATH, encoding="latin1", low_memory=False)

    # Clean severity
    df = df[df["Severity"].isin(VALID_SEVERITY)].copy()

    # Numeric year
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df[df["Year"].between(2010, 2030)]
    df["Year"] = df["Year"].astype(int)

    # Clean coordinates
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")
    valid_coords = (
        df["Latitude"].between(11.5, 18.5) & df["Longitude"].between(74.0, 79.0)
    )
    df["HasCoords"] = valid_coords

    # Normalize district names
    df["DISTRICTNAME"] = df["DISTRICTNAME"].str.strip().str.title()

    # Map weather to cleaner categories
    df["Weather_Clean"] = df["Weather"].map(WEATHER_MAP).fillna("Others")

    # Severity as ordered categorical
    df["Severity"] = pd.Categorical(df["Severity"], categories=SEVERITY_ORDER, ordered=True)

    # Vehicles involved numeric
    df["Noofvehicle_involved"] = pd.to_numeric(df["Noofvehicle_involved"], errors="coerce")

    return df


@st.cache_data(show_spinner=False)
def get_map_data():
    """Return only records with valid Karnataka coordinates."""
    df = load_data()
    return df[df["HasCoords"]].copy()


@st.cache_data(show_spinner=False)
def get_districts():
    df = load_data()
    districts = sorted(df["DISTRICTNAME"].dropna().unique().tolist())
    return districts


@st.cache_data(show_spinner=False)
def get_summary_stats():
    df = load_data()
    stats = {
        "total_accidents": len(df),
        "total_districts": df["DISTRICTNAME"].nunique(),
        "total_years": df["Year"].nunique(),
        "year_range": f"{int(df['Year'].min())} – {int(df['Year'].max())}",
        "fatal_count": int((df["Severity"] == "Fatal").sum()),
        "grievous_count": int((df["Severity"] == "Grievous Injury").sum()),
        "simple_count": int((df["Severity"] == "Simple Injury").sum()),
        "damage_count": int((df["Severity"] == "Damage Only").sum()),
        "valid_coords": int(df["HasCoords"].sum()),
        "most_accidents_district": df["DISTRICTNAME"].value_counts().idxmax(),
        "peak_year": int(df["Year"].value_counts().idxmax()),
    }
    return stats
