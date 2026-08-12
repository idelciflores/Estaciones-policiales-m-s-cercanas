import math
import json
import streamlit as st
import pandas as pd

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

st.set_page_config(page_title="Sistema de Estaciones Policiales")

st.title("Búsqueda de Estaciones Policiales")

try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except FileNotFoundError:
    st.error("No se pudo cargar la base de datos de estaciones (stations.json).")
    st.stop()

st.markdown("### Ingrese su ubicación actual")

col1, col2 = st.columns(2)
with col1:
    lat_input = st.number_input("Latitud", value=14.783300, format="%.6f")
with col2:
    lon_input = st.number_input("Longitud", value=-87.900000, format="%.6f")

if st.button("Buscar estación"):
    for est in estaciones:
        est['distancia'] = haversine(lat_input, lon_input, est['lat'], est['lon'])
    
    cercanas = sorted(estaciones, key=lambda x: x['distancia'])
    estacion_principal = cercanas[0]
    
    st.info(f"Estación más cercana: **{estacion_principal['nombre']}** (a {estacion_principal['distancia']:.2f} km de su posición)")

    st.markdown("#### Estaciones cercanas:")
    for i, est in enumerate(cercanas[:3], 1):
        st.write(f"{i}. {est['nombre']} - {est['distancia']:.2f} km")

    st.markdown("#### Mapa de ubicación")
    
    puntos_mapa = [
        {"lat": lat_input, "lon": lon_input}
    ]
    for est in cercanas[:3]:
        puntos_mapa.append({"lat": est['lat'], "lon": est['lon']})
        
    df_mapa = pd.DataFrame(puntos_mapa)
    st.map(df_mapa, zoom=9)
