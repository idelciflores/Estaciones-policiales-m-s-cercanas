import json
import math
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

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

st.title("Sistema de Geolocalización Policial 👮‍♂️ Honduras")

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

# Cargar json de estaciones policiales
try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except FileNotFoundError:
    st.error("No se encontró 'stations.json'.")
    st.stop()

# Obtención del GPS del navegador
loc = get_geolocation()

if loc and "coords" in loc:
    st.session_state["user_lat"] = loc["coords"]["latitude"]
    st.session_state["user_lon"] = loc["coords"]["longitude"]
    estado_gps = "GPS Real Detectado 📡"
else:
    if "user_lat" not in st.session_state:
        st.session_state["user_lat"] = 14.7951
    if "user_lon" not in st.session_state:
        st.session_state["user_lon"] = -87.8042
    estado_gps = "Ubicación Manual / Esperando GPS ⏳"

col_config, col_destino = st.columns([2, 2])

with col_config:
    st.caption("📍 Coordenadas de origen:")
    col_lat, col_lon = st.columns(2)
    with col_lat:
        user_lat = st.number_input("Latitud", value=float(st.session_state["user_lat"]), format="%.6f", key="input_lat")
    with col_lon:
        user_lon = st.number_input("Longitud", value=float(st.session_state["user_lon"]), format="%.6f", key="input_lon")

st.session_state["user_lat"] = user_lat
st.session_state["user_lon"] = user_lon

# Ordenar estaciones
for est in estaciones:
    est['distancia_directa'] = haversine(user_lat, user_lon, est['lat'], est['lon'])

estaciones_ordenadas = sorted(estaciones, key=lambda x: x['distancia_directa'])
nombres_estaciones = [e['nombre'] for e in estaciones_ordenadas]

if "estacion_seleccionada" not in st.session_state:
    st.session_state["estacion_seleccionada"] = nombres_estaciones[0]

with col_destino:
    estacion_elegida = st.selectbox(
        "Seleccione la Estación Destino:", 
        nombres_estaciones,
        index=nombres_estaciones.index(st.session_state["estacion_seleccionada"]) if st.session_state["estacion_seleccionada"] in nombres_estaciones else 0
    )
    st.session_state["estacion_seleccionada"] = estacion_elegida

estacion_destino = next(e for e in estaciones_ordenadas if e['nombre'] == st.session_state["estacion_seleccionada"])

# Ruta por carretera
puntos_ruta, distancia_ruta_km = obtener_ruta_carretera(
    user_lat, user_lon, 
    estacion_destino['lat'], estacion_destino['lon']
)

# Métricas
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("Origen", estado_gps)
with col_m2:
    st.metric("Estación Destino", estacion_destino['nombre'])
with col_m3:
    st.metric("Distancia por Carretera", f"{distancia_ruta_km:.2f} km")

st.divider()

# Generación del Mapa
m = folium.Map(location=[user_lat, user_lon], zoom_start=13, tiles="CartoDB positron")

# Marcador del usuario
folium.Marker(
    [user_lat, user_lon],
    tooltip="Posición del Usuario",
    icon=folium.Icon(color="blue", icon="user", prefix="fa")
).add_to(m)

# Estaciones
for est in estaciones_ordenadas:
    es_destino = (est['nombre'] == estacion_destino['nombre'])
    color_punto = "#FF0000" if es_destino else "#FFFFFF"
    radio_punto = 10 if es_destino else 7

    folium.CircleMarker(
        location=[est['lat'], est['lon']],
        radius=radio_punto,
        popup=est['nombre'],
        tooltip=f"{est['nombre']} ({est['distancia_directa']:.2f} km)",
        color="#000000",
        weight=2,
        fill=True,
        fill_color=color_punto,
        fill_opacity=0.95
    ).add_to(m)

# Trazado
folium.PolyLine(
    locations=puntos_ruta,
    color="#E74C3C",
    weight=5,
    opacity=0.85
).add_to(m)

m.fit_bounds(puntos_ruta, padding=(30, 30))

mapa_data = st_folium(m, width="100%", height=550, returned_objects=["last_object_clicked"])

if mapa_data and mapa_data.get("last_object_clicked"):
    click_lat = mapa_data["last_object_clicked"]["lat"]
    click_lon = mapa_data["last_object_clicked"]["lng"]
    
    for est in estaciones_ordenadas:
        if abs(est['lat'] - click_lat) < 0.005 and abs(est['lon'] - click_lon) < 0.005:
            if st.session_state["estacion_seleccionada"] != est['nombre']:
                st.session_state["estacion_seleccionada"] = est['nombre']
                st.rerun()
