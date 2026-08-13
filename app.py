import json
import math
import streamlit as st
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
    div[data-testid="stMetricValue"] { font-size: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

st.title("Sistema de Geolocalización Policial")

try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except FileNotFoundError:
    st.error("Error al cargar el archivo stations.json")
    st.stop()

# Captura de geolocalización automática del dispositivo
location = get_geolocation()

col_config, col_destino, col_btn = st.columns([2, 2, 1])

with col_config:
    usar_gps = st.checkbox("Usar GPS automático del dispositivo", value=True)
    
    if usar_gps and location and 'coords' in location:
        user_lat = location['coords']['latitude']
        user_lon = location['coords']['longitude']
        estado_origen = "GPS Detectado"
    else:
        st.caption("Ingrese coordenadas manuales si no dispone de GPS activo:")
        col_lat, col_lon = st.columns(2)
        with col_lat:
            user_lat = st.number_input("Latitud", value=14.783300, format="%.6f")
        with col_lon:
            user_lon = st.number_input("Longitud", value=-87.900000, format="%.6f")
        estado_origen = "Coordenadas Manuales"

# Cálculo dinámico de distancias desde la ubicación del usuario
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

estacion_destino = next(e for e in estaciones_ordenadas if e['nombre'] == estacion_seleccionada)

# Panel de información superior
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("Origen Actual", estado_origen)
with col_m2:
    st.metric("Estación Destino", estacion_destino['nombre'])
with col_m3:
    st.metric("Distancia Directa", f"{estacion_destino['distancia']:.2f} km")

st.divider()

# Mapa a pantalla completa centrado dinámicamente en el origen actual
m = folium.Map(tiles="CartoDB positron")

# Marcador de la posición actual del usuario (GPS o manual)
folium.Marker(
    [user_lat, user_lon],
    tooltip="Su posición actual",
    icon=folium.Icon(color="darkblue", icon="user", prefix="fa")
).add_to(m)

# Marcadores de las estaciones de policía registradas
for est in estaciones_ordenadas:
    es_destino = (est['nombre'] == estacion_destino['nombre'])
    color = "red" if es_destino else "gray"
    
    folium.Marker(
        [est['lat'], est['lon']],
        tooltip=f"{est['nombre']} ({est['distancia']:.2f} km)",
        icon=folium.Icon(color=color, icon="shield", prefix="fa")
    ).add_to(m)

# Trazado directo de la ruta desde tu posición actual hasta la estación seleccionada
linea = [
    [user_lat, user_lon],
    [estacion_destino['lat'], estacion_destino['lon']]
]

folium.PolyLine(
    locations=linea,
    color="#1f77b4",
    weight=5,
    opacity=0.85,
    dash_array='6, 6'
).add_to(m)

# Ajuste automático del encuadre del mapa a la ruta trazada
m.fit_bounds([[user_lat, user_lon], [estacion_destino['lat'], estacion_destino['lon']]], padding=(30, 30))

st_folium(m, width="100%", height=520, returned_objects=[])
