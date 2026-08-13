import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from streamlit_autorefresh import st_autorefresh
import requests
import json

# --- Configuración Pro ---
st.set_page_config(page_title="Navegación Policial", layout="wide", initial_sidebar_state="expanded")

# Inyectar CSS
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .stFolium { width: 100%; height: 80vh !important; }
    </style>
""", unsafe_allow_html=True)

# Refresco automático
st_autorefresh(interval=10000, key="nav_refresh")

# Cache para optimizar carga de estaciones
@st.cache_data
def cargar_estaciones():
    with open('stations.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_legal_route(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    try:
        response = requests.get(url, timeout=3).json()
        if 'routes' in response and response['routes']:
            coords = response['routes'][0]['geometry']['coordinates']
            return [[c[1], c[0]] for c in coords]
    except: return None
    return None

# Carga de datos
estaciones = cargar_estaciones()

# Estado
if 'pos' not in st.session_state: st.session_state.pos = {'lat': 14.7833, 'lon': -87.9000}
loc = get_geolocation()
if loc and 'coords' in loc:
    st.session_state.pos = {'lat': loc['coords']['latitude'], 'lon': loc['coords']['longitude']}

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Panel de Control")
    nombres = [e['nombre'] for e in estaciones]
    sel = st.selectbox("Seleccione Destino:", nombres)
    dest = next(e for e in estaciones if e['nombre'] == sel)
    st.metric("Estado", "🟢 En vivo", delta="GPS Activo")
    st.info("Recalculando ruta automáticamente...")

# --- MAIN ---
ruta = get_legal_route(st.session_state.pos['lat'], st.session_state.pos['lon'], dest['lat'], dest['lon'])

m = folium.Map(location=[st.session_state.pos['lat'], st.session_state.pos['lon']], zoom_start=17, tiles="CartoDB positron")

# Marcadores
folium.Marker([st.session_state.pos['lat'], st.session_state.pos['lon']], 
              icon=folium.Icon(color="blue", icon="user"), tooltip="Tú").add_to(m)
folium.Marker([dest['lat'], dest['lon']], 
              icon=folium.Icon(color="red", icon="shield"), tooltip=dest['nombre']).add_to(m)

# Ruta
if ruta:
    folium.PolyLine(ruta, color="#2980b9", weight=7, opacity=0.9).add_to(m)
    m.fit_bounds([[st.session_state.pos['lat'], st.session_state.pos['lon']], [dest['lat'], dest['lon']]], padding=(50, 50))

st_folium(m, use_container_width=True, height=None)
