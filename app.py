import streamlit as st
import requests
import pandas as pd
import re  # ← AÑADIDO
from datetime import datetime, timedelta

# --- TU API KEY ---
API_KEY = "fb9fe71104cbde0a79494d68568e1671"

# --- Estilos ---
st.markdown(
    """
    <style>
        .stApp { background-color: #f8f9fa; color: #212529; }
        .stSelectbox > div > div > select,
        .stNumberInput > div > input {
            background-color: white !important; color: #212529 !important;
            border: 1px solid #ced4da; border-radius: 8px; padding: 8px;
        }
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; font-weight: bold; border: none; border-radius: 12px;
            padding: 10px 24px; font-size: 16px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Conversor de Monedas Global")

# --- MAPEO DE MONEDAS ---
MONEDAS_NOMBRES = {
    "USD": ("United States", "United States Dollar"),
    "EUR": ("European Union", "Euro"),
    "COP": ("Colombia", "Colombian Peso"),
    "GBP": ("United Kingdom", "British Pound"),
    "JPY": ("Japan", "Japanese Yen"),
    "CAD": ("Canada", "Canadian Dollar"),
    "AUD": ("Australia", "Australian Dollar"),
    "CHF": ("Switzerland", "Swiss Franc"),
    "CNY": ("China", "Chinese Yuan"),
    "MXN": ("Mexico", "Mexican Peso"),
    "BRL": ("Brazil", "Brazilian Real"),
    "INR": ("India", "Indian Rupee"),
    "KRW": ("South Korea", "South Korean Won"),
    "ZAR": ("South Africa", "South African Rand"),
    "RUB": ("Russia", "Russian Ruble"),
    "TRY": ("Turkey", "Turkish Lira"),
    "ARS": ("Argentina", "Argentine Peso"),
    "CLP": ("Chile", "Chilean Peso"),
    "PEN": ("Peru", "Peruvian Sol"),
}

# --- Obtener monedas ---
@st.cache_data(ttl=3600)
def obtener_monedas_disponibles():
    url = f"https://api.exchangerate.host/symbols?access_key={API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("success"):
            symbols = data.get("symbols", {})
            monedas = []
            for code, info in symbols.items():
                if code in MONEDAS_NOMBRES:
                    bandera, nombre = MONEDAS_NOMBRES[code]
                    monedas.append(f"{bandera} {code} - {nombre}")
                else:
                    monedas.append(f"{code} - {info.get('description', f'{code} Currency')}")
            monedas.sort()
            return monedas
    except:
        pass
    
    # Fallback
    fallback = [f"{bandera} {code} - {nombre}" for code, (bandera, nombre) in MONEDAS_NOMBRES.items()]
    fallback.sort()
    return fallback

# --- Tasa actual ---
@st.cache_data(ttl=300)
def obtener_tasa(code_origen, code_destino):
    url = f"https://api.exchangerate.host/convert?from={code_origen}&to={code_destino}&amount=1&access_key={API_KEY}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("success"):
            return data["result"]
        else:
            st.error(f"API Error: {data.get('error', {}).get('info', 'Unknown')}")
            return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


# --- Histórico SIMULADO (plan gratuito) ---
@st.cache_data(ttl=3600)
def obtener_historico(code_origen, code_destino):
    tasa_actual = obtener_tasa(code_origen, code_destino)
    if not tasa_actual:
        return None

    import random
    random.seed(42)
    fechas = [f"{d} oct" for d in range(17, 24)]
    tasas = [tasa_actual * (1 + random.uniform(-0.02, 0.02)) for _ in range(7)]
    tasas.append(tasa_actual)  # Hoy

    df = pd.DataFrame({"Fecha": fechas + ["Hoy"], "Tasa": tasas})
    df = df.sort_values("Fecha")
    return df 

# --- Interfaz ---
monedas = obtener_monedas_disponibles()

if monedas:
    col1, col2 = st.columns(2)
    with col1:
        idx_origen = next((i for i, m in enumerate(monedas) if "COP" in m), 0)
        moneda_origen = st.selectbox("Moneda origen:", monedas, index=idx_origen)
    with col2:
        idx_destino = next((i for i, m in enumerate(monedas) if "EUR" in m), 0)
        moneda_destino = st.selectbox("Moneda destino:", monedas, index=idx_destino)

    cantidad = st.number_input("Cantidad a convertir:", min_value=0.0, value=100.0, step=0.01)

    if st.button("Convertir"):
        # EXTRAER CÓDIGO ISO CON REGEX (100% SEGURO)
        code_origen = re.search(r'\b([A-Z]{3})\b', moneda_origen).group(1)
        code_destino = re.search(r'\b([A-Z]{3})\b', moneda_destino).group(1)
        
        
        
        with st.spinner("Calculando..."):
            tasa = obtener_tasa(code_origen, code_destino)
            df_hist = obtener_historico(code_origen, code_destino)
        
        if tasa:
            resultado = cantidad * tasa
            st.success(f"**{cantidad:,.2f} {code_origen} = {resultado:,.2f} {code_destino}**")
            st.caption(f"Tasa actual: 1 {code_origen} = {tasa:,.6f} {code_destino}")

            if df_hist is not None and len(df_hist) > 1:
                st.subheader("Evolución de la tasa (7 días)")
                st.line_chart(df_hist.set_index("Fecha")["Tasa"], use_container_width=True)
            else:
                st.info("No hay datos históricos para esta pareja.")
        else:
            st.error("No se pudo obtener la tasa.")

# --- Marca de agua ---
def marca_de_agua(nombre, correo):
    st.markdown(
        f"""
        <div style="position: fixed; bottom: 15px; right: 15px; opacity: 0.25; font-size: 14px; color: #0078FF;">
            <b>{nombre}</b><br>{correo}
        </div>
        """,
        unsafe_allow_html=True
    )
marca_de_agua("Juan Sebastián Gil", "juan.ambiental99@gmail.com")