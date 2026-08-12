import json
import math
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

st.set_page_config(
    page_title="Navegación Policial", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo CSS personalizado para limpiar espacio en blanco
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
""", unsafe_allow_html=unsafe_allow_html)

st.title("Sistema de Geolocalización y Cobertura Policial")

try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except FileNotFoundError:
    st.error("Error al cargar el archivo de datos (stations.json).")
    st.stop()

# Captura de geolocalización
location = get_geolocation()

if location:
    user_lat = location['coords']['latitude']
    user_lon = location['coords']['longitude']
else:
    # Coordenadas base por defecto (Siguatepeque / MeÁmbar)
    user_lat = 14.783300
    user_lon = -87.900000

# Cálculo de distancias
for est in estaciones:
    est['distancia'] = haversine(user_lat, user_lon, est['lat'], est['lon'])

estaciones_ordenadas = sorted(estaciones, key=lambda x: x['distancia'])

# Panel de control superior
col_selector, col_btn = st.columns([3, 1])

with col_selector:
    nombres = [e['nombre'] for e in estaciones_ordenadas]
    estacion_seleccionada = st.selectbox("Seleccione la estación destino:", nombres)

with col_btn:
    st.write(" ")
    st.write(" ")
    if st.button("Actualizar posición", use_container_width=True):
        st.rerun()

estacion_destino = next(e for e in estaciones_ordenadas if e['nombre'] == estacion_seleccionada)

# Métricas principales
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("Estación Seleccionada", estacion_destino['nombre'])
with col_m2:
    st.metric("Distancia Directa", f"{estacion_destino['distancia']:.2f} km")
with col_m3:
    st.metric("Estado de Señal GPS", "Activa" if location else "Por defecto")

st.divider()

# Columna izquierda: Tabla organizada | Columna derecha: Mapa limpio
col_tabla, col_mapa = st.columns([1, 2])

with col_tabla:
    st.markdown("#### Estaciones Cercanas")
    df_estaciones = pd.DataFrame(estaciones_ordenadas)[['nombre', 'distancia']]
    df_estaciones.columns = ['Estación', 'Distancia (km)']
    df_estaciones['Distancia (km)'] = df_estaciones['Distancia (km)'].round(2)
    st.dataframe(df_estaciones, use_container_width=True, height=400)

with col_mapa:
    st.markdown("#### Ruta de Cobertura")
    
    # Mapa base con estilo minimalista
    m = folium.Map(
        location=[user_lat, user_lon], 
        zoom_start=11, 
        tiles="CartoDB positron"
    )

    # Ubicación del usuario
    folium.Marker(
        [user_lat, user_lon],
        tooltip="Su ubicación actual",
        icon=folium.Icon(color="darkblue", icon="user", prefix="fa")
    ).add_to(m)

    # Ubicaciones de las estaciones
    for est in estaciones_ordenadas:
        es_destino = est['nombre'] == estacion_destino['nombre']
        color = "red" if es_destino else "gray"
        
        folium.Marker(
            [est['lat'], est['lon']],
            tooltip=f"{est['nombre']} ({est['distancia']:.2f} km)",
            icon=folium.Icon(color=color, icon="shield", prefix="fa")
        ).add_to(m)

    # Línea de trazado recta punteada
    linea = [
        [user_lat, user_lon],
        [estacion_destino['lat'], estacion_destino['lon']]
    ]
    
    folium.PolyLine(
        locations=linea,
        color="#1f77b4",
        weight=4,
        opacity=0.8,
        dash_array='6, 6'
    ).add_to(m)

    st_folium(m, width="100%", height=400, returned_objects=[])
