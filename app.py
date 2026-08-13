import math
import json
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="Emergencia Policial HN", layout="wide")

# Estilos de Emergencia (Botones grandes, claros)
st.markdown("""
    <style>
    div.stButton > button { font-size: 20px; height: 3em; width: 100%; color: white; background-color: #d32f2f; }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN GPS (Intenta alta precisión) ---
if "user_lat" not in st.session_state:
    st.session_state["user_lat"] = 14.7951 # Default
    st.session_state["user_lon"] = -87.8042
    # Intentar obtener GPS con alta precisión
    loc = get_geolocation(timeout=5000, enableHighAccuracy=True)
    if loc and "coords" in loc:
        st.session_state["user_lat"] = loc["coords"]["latitude"]
        st.session_state["user_lon"] = loc["coords"]["longitude"]

# --- LÓGICA ---
try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except: st.stop()

# Cálculo rápido de distancia (Sin editar coordenadas, esto es automático)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Ordenar por cercanía (El usuario no elige, la app elige la más cerca para ahorrar tiempo)
for est in estaciones:
    est['dist'] = haversine(st.session_state["user_lat"], st.session_state["user_lon"], est['lat'], est['lon'])
estaciones = sorted(estaciones, key=lambda x: x['dist'])
mas_cercana = estaciones[0]

# --- UI DE EMERGENCIA ---
st.title("🚨 Botón de Emergencia Policial")
st.write(f"### Estación más cercana: **{mas_cercana['nombre']}**")

# Mapa
m = folium.Map(location=[st.session_state["user_lat"], st.session_state["user_lon"]], zoom_start=15)
folium.Marker([st.session_state["user_lat"], st.session_state["user_lon"]], icon=folium.Icon(color="blue", icon="user")).add_to(m)
folium.Marker([mas_cercana['lat'], mas_cercana['lon']], icon=folium.Icon(color="red", icon="shield")).add_to(m)

# El mapa interactivo es el ÚNICO método de corrección
mapa_data = st_folium(m, width="100%", height=400)

if mapa_data and mapa_data.get("last_clicked"):
    st.session_state["user_lat"] = mapa_data["last_clicked"]["lat"]
    st.session_state["user_lon"] = mapa_data["last_clicked"]["lng"]
    st.rerun()

st.warning("⚠️ Si la ubicación es incorrecta, **toca en el mapa donde estás realmente** y se recalculará al instante.")
