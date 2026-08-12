import json
import math
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# Configuración inicial del layout en Streamlit 💻
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

# Cálculo Haversine para respaldo de distancia recta 📏
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Obtención de ruta vial exacta con la API de OSRM 🛣️
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

# Cargar las estaciones desde el archivo json 📄
try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except FileNotFoundError:
    st.error("Error: No se encontró el archivo 'stations.json'.")
    st.stop()

# Captura de geolocalización dinámica 📡
location = get_geolocation()

col_config, col_destino, col_btn = st.columns([2, 2, 1])

with col_config:
    usar_gps = st.checkbox("Usar GPS automático del dispositivo", value=True)
    
    if usar_gps and location and 'coords' in location:
        user_lat = location['coords']['latitude']
        user_lon = location['coords']['longitude']
        estado_origen = "GPS Detectado 📡"
    else:
        st.caption("Ingrese coordenadas manuales si no dispone de GPS activo:")
        col_lat, col_lon = st.columns(2)
        with col_lat:
            user_lat = st.number_input("Latitud", value=14.783300, format="%.6f")
        with col_lon:
            user_lon = st.number_input("Longitud", value=-87.900000, format="%.6f")
        estado_origen = "Coordenadas Manuales 📌"

# Calcular distancias iniciales 📊
for est in estaciones:
    est['distancia_directa'] = haversine(user_lat, user_lon, est['lat'], est['lon'])

estaciones_ordenadas = sorted(estaciones, key=lambda x: x['distancia_directa'])

# Desplegable para elegir destino (priorizando Sigua si está presente) 🔎
with col_destino:
    nombres_estaciones = [e['nombre'] for e in estaciones_ordenadas]
    index_sigua = 0
    for idx, e in enumerate(nombres_estaciones):
        if "sigua" in e.lower():
            index_sigua = idx
            break

    estacion_seleccionada = st.selectbox(
        "Seleccione la Estación Destino:", 
        nombres_estaciones,
        index=index_sigua
    )

with col_btn:
    st.write(" ")
    st.write(" ")
    if st.button("Actualizar posición 🔄", use_container_width=True):
        st.rerun()

estacion_destino = next(e for e in estaciones_ordenadas if e['nombre'] == estacion_seleccionada)

# Generar trazo de la ruta vial actual 🚘
puntos_ruta, distancia_ruta_km = obtener_ruta_carretera(
    user_lat, user_lon, 
    estacion_destino['lat'], estacion_destino['lon']
)

# Métricas informativas 📈
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("Origen Actual", estado_origen)
with col_m2:
    st.metric("Estación Destino", estacion_destino['nombre'])
with col_m3:
    st.metric("Distancia por Carretera", f"{distancia_ruta_km:.2f} km")

st.divider()

# Creación del mapa 🗺️
m = folium.Map(location=[user_lat, user_lon], zoom_start=9, tiles="CartoDB positron")

# Ubicación actual del usuario 👤
folium.Marker(
    [user_lat, user_lon],
    tooltip="Su posición actual",
    icon=folium.Icon(color="darkblue", icon="user", prefix="fa")
).add_to(m)

# Dibujar estaciones: Blancas ⚪ y la seleccionada en Rojo 🔴
for est in estaciones_ordenadas:
    es_destino = (est['nombre'] == estacion_destino['nombre'])
    
    color_punto = "#FF0000" if es_destino else "#FFFFFF"
    radio_punto = 9 if es_destino else 6

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

# Dibujar la ruta que sigue las carreteras reales 🛣️
folium.PolyLine(
    locations=puntos_ruta,
    color="#E74C3C",
    weight=5,
    opacity=0.85
).add_to(m)

# Ajuste dinámico de cámara según el avance de la persona 🎥
m.fit_bounds(puntos_ruta, padding=(30, 30))

st_folium(m, width="100%", height=550, returned_objects=[])
