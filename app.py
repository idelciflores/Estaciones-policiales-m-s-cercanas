import json
import math
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# Configuración inicial de la página
st.set_page_config(page_title="Navegación Policial Honduras", layout="wide")

# Inicialización de variables en estado
if 'user_lat' not in st.session_state: st.session_state.user_lat = 14.783300
if 'user_lon' not in st.session_state: st.session_state.user_lon = -87.900000

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Carga de datos
try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except FileNotFoundError:
    st.error("Error: No se encuentra el archivo stations.json")
    st.stop()

st.title("Sistema de Geolocalización Policial")

# Sección de configuración de ubicación
col_config, col_opciones = st.columns([1, 1])

with col_config:
    st.subheader("Configuración de Origen")
    modo_gps = st.checkbox("Usar GPS del dispositivo", value=True)
    
    if modo_gps:
        loc = get_geolocation()
        if loc and 'coords' in loc:
            st.session_state.user_lat = loc['coords']['latitude']
            st.session_state.user_lon = loc['coords']['longitude']
            st.success(f"GPS Activo: {st.session_state.user_lat:.5f}, {st.session_state.user_lon:.5f}")
        else:
            st.info("Esperando señal GPS... si no carga, usa los campos manuales abajo.")
            
    # Entrada manual para corrección inmediata
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.user_lat = st.number_input("Latitud Manual:", value=st.session_state.user_lat, format="%.6f")
    with c2:
        st.session_state.user_lon = st.number_input("Longitud Manual:", value=st.session_state.user_lon, format="%.6f")

# Cálculos de distancia
for est in estaciones:
    est['distancia'] = haversine(st.session_state.user_lat, st.session_state.user_lon, est['lat'], est['lon'])

estaciones_ordenadas = sorted(estaciones, key=lambda x: x['distancia'])

with col_opciones:
    st.subheader("Selección de Destino")
    nombres = [e['nombre'] for e in estaciones_ordenadas]
    seleccion = st.selectbox("Seleccione la Estación:", nombres)
    estacion_destino = next(e for e in estaciones_ordenadas if e['nombre'] == seleccion)

# Métricas visuales
c1, c2, c3 = st.columns(3)
c1.metric("Origen", "Configurado")
c2.metric("Destino", estacion_destino['nombre'])
c3.metric("Distancia", f"{estacion_destino['distancia']:.2f} km")

st.divider()

# Mapa
m = folium.Map(location=[st.session_state.user_lat, st.session_state.user_lon], zoom_start=12)

# Marcador usuario
folium.Marker(
    [st.session_state.user_lat, st.session_state.user_lon], 
    tooltip="Su posición", 
    icon=folium.Icon(color="darkblue", icon="user")
).add_to(m)

# Marcadores estaciones
for est in estaciones_ordenadas:
    es_destino = (est['nombre'] == estacion_destino['nombre'])
    folium.Marker(
        [est['lat'], est['lon']], 
        tooltip=f"{est['nombre']} ({est['distancia']:.2f} km)",
        icon=folium.Icon(color="red" if es_destino else "gray", icon="shield")
    ).add_to(m)

# Trazado ruta
folium.PolyLine(
    [[st.session_state.user_lat, st.session_state.user_lon], [estacion_destino['lat'], estacion_destino['lon']]],
    color="#1f77b4", weight=5, dash_array='6, 6'
).add_to(m)

m.fit_bounds([[st.session_state.user_lat, st.session_state.user_lon], [estacion_destino['lat'], estacion_destino['lon']]], padding=(30, 30))

st_folium(m, width="100%", height=500)

if st.button("Actualizar Mapa / Forzar Recálculo"):
    st.rerun()
