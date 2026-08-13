import json
import math
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# Configuración de página
st.set_page_config(page_title="Navegación Policial Honduras", layout="wide", initial_sidebar_state="collapsed")

# Inicializar estado para guardar la ubicación
if 'user_location' not in st.session_state:
    st.session_state.user_location = None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

st.title("Sistema de Geolocalización Policial")

try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except FileNotFoundError:
    st.error("Error al cargar el archivo stations.json")
    st.stop()

# 1. Intentar capturar la geolocalización
location = get_geolocation()

# Si obtenemos datos nuevos y son válidos, los guardamos en el session_state
if location and 'coords' in location:
    st.session_state.user_location = {
        'lat': location['coords']['latitude'],
        'lon': location['coords']['longitude']
    }

# Lógica de la interfaz
col_config, col_destino, col_btn = st.columns([2, 2, 1])

with col_config:
    usar_gps = st.checkbox("Usar GPS automático del dispositivo", value=True)
    
    # Verificamos si tenemos datos en el session_state
    if usar_gps and st.session_state.user_location:
        user_lat = st.session_state.user_location['lat']
        user_lon = st.session_state.user_location['lon']
        estado_origen = "GPS Detectado"
        st.success(f"Ubicación capturada: {user_lat:.4f}, {user_lon:.4f}")
    else:
        # Si no hay GPS aún, pedimos manual o mostramos mensaje
        if usar_gps:
            st.warning("Esperando señal GPS... haz clic en 'Actualizar posición' si no carga.")
        
        col_lat, col_lon = st.columns(2)
        with col_lat:
            user_lat = st.number_input("Latitud", value=14.783300, format="%.6f")
        with col_lon:
            user_lon = st.number_input("Longitud", value=-87.900000, format="%.6f")
        estado_origen = "Coordenadas Manuales"

# Cálculo de distancias
for est in estaciones:
    est['distancia'] = haversine(user_lat, user_lon, est['lat'], est['lon'])
estaciones_ordenadas = sorted(estaciones, key=lambda x: x['distancia'])

with col_destino:
    nombres_estaciones = [e['nombre'] for e in estaciones_ordenadas]
    estacion_seleccionada = st.selectbox("Seleccione la Estación Destino:", nombres_estaciones)

with col_btn:
    st.write(" ")
    st.write(" ")
    if st.button("Actualizar posición", use_container_width=True):
        st.rerun()

# Lógica de visualización
estacion_destino = next(e for e in estaciones_ordenadas if e['nombre'] == estacion_seleccionada)

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Origen Actual", estado_origen)
col_m2.metric("Estación Destino", estacion_destino['nombre'])
col_m3.metric("Distancia", f"{estacion_destino['distancia']:.2f} km")

st.divider()

# Mapa
m = folium.Map(tiles="CartoDB positron")
folium.Marker([user_lat, user_lon], tooltip="Su posición actual", icon=folium.Icon(color="darkblue", icon="user", prefix="fa")).add_to(m)

for est in estaciones_ordenadas:
    es_destino = (est['nombre'] == estacion_destino['nombre'])
    folium.Marker([est['lat'], est['lon']], tooltip=f"{est['nombre']}", icon=folium.Icon(color="red" if es_destino else "gray", icon="shield", prefix="fa")).add_to(m)

folium.PolyLine([[user_lat, user_lon], [estacion_destino['lat'], estacion_destino['lon']]], color="#1f77b4", weight=5, dash_array='6, 6').add_to(m)

m.fit_bounds([[user_lat, user_lon], [estacion_destino['lat'], estacion_destino['lon']]], padding=(30, 30))
st_folium(m, width="100%", height=520)
