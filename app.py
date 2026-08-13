import math
import json  # ¡Importante! Faltaba este
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

st.set_page_config(
    page_title="Navegación Policial Honduras", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos profesionales
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

st.title("👮‍♂️ Sistema de Geolocalización Policial - Honduras")

# --- FUNCIONES ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def obtener_ruta_carretera(lat_origen, lon_origen, lat_destino, lon_destino):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon_origen},{lat_origen};{lon_destino},{lat_destino}?overview=full&geometries=geojson"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            coords = data['routes'][0]['geometry']['coordinates']
            puntos_ruta = [[c[1], c[0]] for c in coords]
            distancia_km = data['routes'][0]['distance'] / 1000.0
            return puntos_ruta, distancia_km
    except Exception:
        pass
    return [[lat_origen, lon_origen], [lat_destino, lon_destino]], haversine(lat_origen, lon_origen, lat_destino, lon_destino)

# --- CARGA DE DATOS ---
try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except FileNotFoundError:
    st.error("Error: No se encontró 'stations.json'.")
    st.stop()

# --- LÓGICA DE UBICACIÓN (CORREGIDA PARA SER ESTABLE) ---
st.subheader("Configuración de Origen")
col_tipo, col_lat_in, col_lon_in = st.columns([1, 1, 1])

# Selector de modo
with col_tipo:
    modo = st.radio("Seleccione modo de ubicación:", ["Manual", "GPS Automático"], index=0)

# Inicializar estados si no existen
if "user_lat" not in st.session_state: st.session_state["user_lat"] = 14.7951
if "user_lon" not in st.session_state: st.session_state["user_lon"] = -87.8042

if modo == "GPS Automático":
    loc = get_geolocation()
    if loc and "coords" in loc:
        st.session_state["user_lat"] = loc["coords"]["latitude"]
        st.session_state["user_lon"] = loc["coords"]["longitude"]
        estado_gps = "GPS Real Detectado 📡"
    else:
        estado_gps = "Esperando señal GPS... ⏳"
else:
    estado_gps = "Modo Manual ✍️"
    with col_lat_in:
        st.session_state["user_lat"] = st.number_input("Latitud", value=st.session_state["user_lat"], format="%.6f")
    with col_lon_in:
        st.session_state["user_lon"] = st.number_input("Longitud", value=st.session_state["user_lon"], format="%.6f")

user_lat = st.session_state["user_lat"]
user_lon = st.session_state["user_lon"]

# --- CÁLCULO Y DESTINO ---
for est in estaciones:
    est['distancia_directa'] = haversine(user_lat, user_lon, est['lat'], est['lon'])

estaciones_ordenadas = sorted(estaciones, key=lambda x: x['distancia_directa'])
nombres_estaciones = [e['nombre'] for e in estaciones_ordenadas]

if "estacion_seleccionada" not in st.session_state:
    st.session_state["estacion_seleccionada"] = nombres_estaciones[0]

estacion_elegida = st.selectbox("Seleccione la Estación Destino:", nombres_estaciones)
st.session_state["estacion_seleccionada"] = estacion_elegida

estacion_destino = next(e for e in estaciones_ordenadas if e['nombre'] == estacion_elegida)

# Obtener ruta
puntos_ruta, distancia_ruta_km = obtener_ruta_carretera(
    user_lat, user_lon, estacion_destino['lat'], estacion_destino['lon']
)

# Métricas
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Origen", estado_gps)
col_m2.metric("Destino", estacion_destino['nombre'])
col_m3.metric("Distancia", f"{distancia_ruta_km:.2f} km")

# --- MAPA ---
m = folium.Map(location=[user_lat, user_lon], zoom_start=13, tiles="CartoDB positron")

folium.Marker([user_lat, user_lon], tooltip="Usuario", icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(m)

for est in estaciones_ordenadas:
    es_destino = (est['nombre'] == estacion_destino['nombre'])
    folium.CircleMarker(
        location=[est['lat'], est['lon']],
        radius=10 if es_destino else 7,
        popup=est['nombre'],
        tooltip=f"{est['nombre']} ({est['distancia_directa']:.2f} km)",
        color="black",
        fill=True,
        fill_color="#FF0000" if es_destino else "#FFFFFF"
    ).add_to(m)

folium.PolyLine(locations=puntos_ruta, color="#E74C3C", weight=5, opacity=0.85).add_to(m)
m.fit_bounds(puntos_ruta, padding=(30, 30))

st_folium(m, width="100%", height=550)
