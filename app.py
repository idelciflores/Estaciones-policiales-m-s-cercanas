import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from streamlit_autorefresh import st_autorefresh
import requests
import json

# --- Configuración ---
st.set_page_config(page_title="Navegación Policial", layout="wide")

# Refresco automático cada 10s
st_autorefresh(interval=10000, key="nav_refresh")

@st.cache_data
def cargar_estaciones():
    try:
        with open('stations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_legal_route(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    try:
        response = requests.get(url, timeout=3).json()
        if 'routes' in response and response['routes']:
            coords = response['routes'][0]['geometry']['coordinates']
            return [[c[1], c[0]] for c in coords]
    except: return None
    return None

estaciones = cargar_estaciones()

# Estado
if 'pos' not in st.session_state: st.session_state.pos = {'lat': 14.7833, 'lon': -87.9000}
loc = get_geolocation()
if loc and 'coords' in loc:
    st.session_state.pos = {'lat': loc['coords']['latitude'], 'lon': loc['coords']['longitude']}

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Panel de Control")
    if estaciones:
        nombres = [e['nombre'] for e in estaciones]
        sel = st.selectbox("Seleccione Destino:", nombres)
        dest = next(e for e in estaciones if e['nombre'] == sel)
    else:
        st.error("No se encontraron estaciones (revisa stations.json)")
        dest = {'lat': 14.7833, 'lon': -87.9000, 'nombre': 'Error'}
    
    st.metric("Estado", "🟢 En vivo")

# --- MAIN (Mapa) ---
ruta = get_legal_route(st.session_state.pos['lat'], st.session_state.pos['lon'], dest['lat'], dest['lon'])

# Crear mapa
m = folium.Map(location=[st.session_state.pos['lat'], st.session_state.pos['lon']], zoom_start=15)

# Marcadores
folium.Marker([st.session_state.pos['lat'], st.session_state.pos['lon']], 
              icon=folium.Icon(color="blue", icon="user")).add_to(m)
folium.Marker([dest['lat'], dest['lon']], 
              icon=folium.Icon(color="red", icon="shield")).add_to(m)

# Ruta
if ruta:
    folium.PolyLine(ruta, color="#2980b9", weight=7, opacity=0.9).add_to(m)

# RENDERIZADO FORZADO:
# Usamos width=100% y un height fijo en pixeles para asegurar que se dibuje
st.subheader("Mapa de Navegación")
st_folium(m, width=1000, height=600)
