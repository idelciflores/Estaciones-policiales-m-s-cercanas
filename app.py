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
    page_title="Navegación Policial Honduras", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; }
    </style>
""", unsafe_allow_html=True)

st.title("Sistema de Geolocalización y Cobertura Policial")

try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except FileNotFoundError:
    st.error("Error al cargar el archivo de datos (stations.json).")
    st.stop()

# Captura de geolocalización GPS
location = get_geolocation()

if location and 'coords' in location:
    user_lat = location['coords']['latitude']
    user_lon = location['coords']['longitude']
else:
    # Coordenadas predeterminadas (Zona MeÁmbar / Siguatepeque)
    user_lat = 14.783300
    user_lon = -87.900000

# Calcular distancia para cada estación
for est in estaciones:
    est['distancia'] = haversine(user_lat, user_lon, est['lat'], est['lon'])

estaciones_ordenadas = sorted(estaciones, key=lambda x: x['distancia'])

# Controles de búsqueda y filtrado
col_buscar, col_select, col_btn = st.columns([2, 3, 1])

with col_buscar:
    filtro_texto = st.text_input("Filtrar por ciudad o nombre:", placeholder="Ej: Sigua, Tegus, Comayagua...")

# Aplicar filtro a las estaciones
if filtro_texto.strip():
    estaciones_filtradas = [
        e for e in estaciones_ordenadas 
        if filtro_texto.lower() in e['nombre'].lower()
    ]
    if not estaciones_filtradas:
        st.warning(f"No se encontraron estaciones que coincidan con '{filtro_texto}'. Mostrando todas.")
        estaciones_filtradas = estaciones_ordenadas
else:
    estaciones_filtradas = estaciones_ordenadas

with col_select:
    nombres_filtrados = [e['nombre'] for e in estaciones_filtradas]
    estacion_seleccionada = st.selectbox("Seleccione la estación destino:", nombres_filtrados)

with col_btn:
    st.write(" ")
    st.write(" ")
    if st.button("Actualizar posición", use_container_width=True):
        st.rerun()

estacion_destino = next(e for e in estaciones_ordenadas if e['nombre'] == estacion_seleccionada)

# Métricas superiores
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("Estación Seleccionada", estacion_destino['nombre'])
with col_m2:
    st.metric("Distancia Directa", f"{estacion_destino['distancia']:.2f} km")
with col_m3:
    st.metric("Estado GPS", "GPS Activo" if location else "Ubicación Base")

st.divider()

# Columna izquierda: Tabla filtrada | Columna derecha: Mapa dinámico
col_tabla, col_mapa = st.columns([1, 2])

with col_tabla:
    st.markdown("#### Estaciones Coincidentes")
    df_estaciones = pd.DataFrame(estaciones_filtradas)[['nombre', 'distancia']]
    df_estaciones.columns = ['Estación', 'Distancia (km)']
    df_estaciones['Distancia (km)'] = df_estaciones['Distancia (km)'].round(2)
    st.dataframe(df_estaciones, use_container_width=True, height=420)

with col_mapa:
    st.markdown("#### Ruta de Cobertura")
    
    m = folium.Map(tiles="CartoDB positron")

    # Marcador del usuario
    folium.Marker(
        [user_lat, user_lon],
        tooltip="Su ubicación actual",
        icon=folium.Icon(color="darkblue", icon="user", prefix="fa")
    ).add_to(m)

    # Marcadores de estaciones
    for est in estaciones_filtradas:
        es_destino = (est['nombre'] == estacion_destino['nombre'])
        color = "red" if es_destino else "gray"
        
        folium.Marker(
            [est['lat'], est['lon']],
            tooltip=f"{est['nombre']} ({est['distancia']:.2f} km)",
            icon=folium.Icon(color=color, icon="shield", prefix="fa")
        ).add_to(m)

    # Trazado de línea recta hasta la estación destino seleccionada
    linea = [
        [user_lat, user_lon],
        [estacion_destino['lat'], estacion_destino['lon']]
    ]
    
    folium.PolyLine(
        locations=linea,
        color="#1f77b4",
        weight=4,
        opacity=0.85,
        dash_array='6, 6'
    ).add_to(m)

    # Encuadre automático del mapa para mostrar al usuario y el destino seleccionado
    m.fit_bounds([[user_lat, user_lon], [estacion_destino['lat'], estacion_destino['lon']]], padding=(30, 30))

    st_folium(m, width="100%", height=420, returned_objects=[])
