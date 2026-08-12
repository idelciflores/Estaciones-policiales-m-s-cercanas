import streamlit as st
import math
import json

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

st.title("Busqueda de estaciones policiales")

try:
    with open('stations.json', 'r', encoding='utf-8') as f:
        estaciones = json.load(f)
except FileNotFoundError:
    st.error("No se encuentra el archivo stations.json")
    st.stop()

lat_input = st.number_input("Ingrese latitud", value=14.464, format="%.6f")
lon_input = st.number_input("Ingrese longitud", value=-87.643, format="%.6f")

if st.button("Buscar"):
    for est in estaciones:
        est['distancia'] = haversine(lat_input, lon_input, est['lat'], est['lon'])
    
    cercanas = sorted(estaciones, key=lambda x: x['distancia'])
    
    st.subheader("Las 3 estaciones mas cercanas:")
    for est in cercanas[:3]:
        st.write(f"{est['nombre']} - Distancia: {est['distancia']:.2f} km")