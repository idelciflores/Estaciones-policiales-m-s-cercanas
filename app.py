import math
import json
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

st.set_page_config(page_title="Navegación Policial HN", layout="wide")

# Estilos profesionales (limpios)
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

st.title("👮‍♂️ Sistema de Geolocalización Policial")

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
        res = requests.get(url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            coords = data['routes'][0]['geometry']['coordinates']
            return [[c[1], c[0]] for c in coords], data['routes'][0]['distance'] / 1000.0
    except: pass
    return [[lat_origen, lon_origen], [lat_destino, lon_destino]], haversine(lat_origen, lon_origen, lat_destino, lon_destino)

# --- CARGA DE DATOS ---
try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except:
    st.error("Error al cargar estaciones.")
    st.stop()

# --- LÓGICA DE UBICACIÓN (PROFESIONAL) ---
# Intentamos obtener la ubicación al cargar
loc = get_geolocation()

if "user_lat" not in st.session_state:
    st.session_state["user_lat"] = 14.7951 # Default centro Honduras
    st.session_state["user_lon"] = -87.8042

# Actualizar si el GPS responde
if loc and "coords" in loc:
    st.session_state["user_lat"] = loc["coords"]["latitude"]
    st.session_state["user_lon"] = loc["coords"]["longitude"]
    st.success("✅ Ubicación GPS detectada")
else:
    st.warning("⚠️ No se pudo acceder al GPS. Usando ubicación base. Permita la ubicación en su navegador.")

# Botón discreto para refrescar o forzar ubicación
if st.button("🔄 Actualizar mi ubicación"):
    st.rerun()

# --- SELECCIÓN Y CÁLCULO ---
user_lat = st.session_state["user_lat"]
user_lon = st.session_state["user_lon"]

# Calcular distancias
for est in estaciones:
    est['dist'] = haversine(user_lat, user_lon, est['lat'], est['lon'])

estaciones_ordenadas = sorted(estaciones, key=lambda x: x['dist'])

# Selector de destino
nombres = [e['nombre'] for e in estaciones_ordenadas]
seleccion = st.selectbox("Seleccione la Estación Destino:", nombres)
est_destino = next(e for e in estaciones_ordenadas if e['nombre'] == seleccion)

# Obtener ruta
puntos, dist_km = obtener_ruta_carretera(user_lat, user_lon, est_destino['lat'], est_destino['lon'])

# Métricas
col1, col2 = st.columns(2)
col1.metric("Distancia", f"{dist_km:.2f} km")
col2.metric("Estación más cercana", estaciones_ordenadas[0]['nombre'])

# --- MAPA ---
m = folium.Map(location=[user_lat, user_lon], zoom_start=12, tiles="CartoDB positron")
folium.Marker([user_lat, user_lon], icon=folium.Icon(color="blue", icon="user", prefix="fa"), tooltip="Tú").add_to(m)

# Marcadores
for est in estaciones_ordenadas:
    folium.CircleMarker(
        [est['lat'], est['lon']],
        radius=8,
        color="red" if est['nombre'] == seleccion else "gray",
        fill=True,
        fill_color="red" if est['nombre'] == seleccion else "white",
        tooltip=est['nombre']
    ).add_to(m)

folium.PolyLine(puntos, color="#E74C3C", weight=5).add_to(m)
m.fit_bounds(puntos, padding=(30, 30))

st_folium(m, width="100%", height=500)

# Opcional: Ajuste manual oculto
with st.expander("¿Precisión incorrecta? Ajustar coordenadas"):
    st.session_state["user_lat"] = st.number_input("Latitud", value=float(st.session_state["user_lat"]), format="%.6f")
    st.session_state["user_lon"] = st.number_input("Longitud", value=float(st.session_state["user_lon"]), format="%.6f")
