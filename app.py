import json
import math
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# 📏 Función para calcular distancia haversine en kilómetros
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ⚙️ Configuración inicial de la página
st.set_page_config(
    page_title="Navegación Policial Honduras 🇭🇳", 
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="👮‍♂️"
)

# 🎨 Estilos personalizados
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; }
    </style>
""", unsafe_allow_html=True)

st.title("🚨 Sistema de Geolocalización Policial")

# 📂 Carga de las estaciones desde el archivo JSON
try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except FileNotFoundError:
    st.error("❌ Error: No se encontró el archivo 'stations.json'. Asegúrate de que esté en el mismo directorio.")
    st.stop()
except json.JSONDecodeError:
    st.error("❌ Error: El archivo 'stations.json' tiene un formato JSON inválido.")
    st.stop()

# 📍 Captura de geolocalización automática del dispositivo
location = get_geolocation()

col_config, col_destino, col_btn = st.columns([2, 2, 1])

with col_config:
    usar_gps = st.checkbox("📡 Usar GPS automático del dispositivo", value=True)
    
    if usar_gps and location and 'coords' in location and location['coords']:
        user_lat = float(location['coords']['latitude'])
        user_lon = float(location['coords']['longitude'])
        estado_origen = "GPS Detectado 🛰️"
    else:
        st.caption("📍 Ingrese coordenadas manuales si no dispone de GPS activo:")
        col_lat, col_lon = st.columns(2)
        with col_lat:
            user_lat = st.number_input("Latitud", value=14.783300, format="%.6f")
        with col_lon:
            user_lon = st.number_input("Longitud", value=-87.900000, format="%.6f")
        estado_origen = "Coordenadas Manuales ✍️"

# 📐 Cálculo dinámico de distancias
for est in estaciones:
    est['distancia'] = haversine(user_lat, user_lon, float(est['lat']), float(est['lon']))

# 🗂️ Ordenar estaciones de la más cercana a la más lejana
estaciones_ordenadas = sorted(estaciones, key=lambda x: x['distancia'])

with col_destino:
    nombres_estaciones = [e['nombre'] for e in estaciones_ordenadas]
    estacion_seleccionada = st.selectbox("🎯 Seleccione la Estación Destino:", nombres_estaciones)

with col_btn:
    st.write(" ")
    st.write(" ")
    if st.button("🔄 Actualizar posición", use_container_width=True):
        st.rerun()

# 📌 Obtener datos de la estación destino elegida
estacion_destino = next(e for e in estaciones_ordenadas if e['nombre'] == estacion_seleccionada)

# 📊 Panel de métricas superior
col_m1, col_m2, col_m3 = st.columns(3)
with col_m1:
    st.metric("Origen Actual", estado_origen)
with col_m2:
    st.metric("Estación Destino", estacion_destino['nombre'])
with col_m3:
    st.metric("Distancia Directa", f"{estacion_destino['distancia']:.2f} km")

st.divider()

# 🗺️ Inicialización del mapa Folium
m = folium.Map(location=[user_lat, user_lon], zoom_start=12, tiles="CartoDB positron")

# 👤 Marcador de la posición actual del usuario
folium.Marker(
    [user_lat, user_lon],
    tooltip="Su posición actual",
    popup="<b>Su Ubicación</b>",
    icon=folium.Icon(color="darkblue", icon="user", prefix="fa")
).add_to(m)

# 🏢 Marcadores para las estaciones policiales
for est in estaciones_ordenadas:
    es_destino = (est['nombre'] == estacion_destino['nombre'])
    color = "red" if es_destino else "gray"
    
    folium.Marker(
        [float(est['lat']), float(est['lon'])],
        tooltip=f"{est['nombre']} ({est['distancia']:.2f} km)",
        popup=f"<b>{est['nombre']}</b><br>Distancia: {est['distancia']:.2f} km",
        icon=folium.Icon(color=color, icon="shield", prefix="fa")
    ).add_to(m)

# 🛣️ Trazado de línea directa hacia el destino
linea = [
    [user_lat, user_lon],
    [float(estacion_destino['lat']), float(estacion_destino['lon'])]
]

folium.PolyLine(
    locations=linea,
    color="#1f77b4",
    weight=5,
    opacity=0.85,
    dash_array='6, 6'
).add_to(m)

# 🔍 Ajuste del encuadre automático a la ruta
m.fit_bounds([[user_lat, user_lon], [float(estacion_destino['lat']), float(estacion_destino['lon'])]], padding=(30, 30))

# 🖥️ Renderizado del mapa en Streamlit
st_folium(m, width="100%", height=520, returned_objects=[])
