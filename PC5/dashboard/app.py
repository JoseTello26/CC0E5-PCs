import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
import time
from datetime import datetime, timedelta

# --- Configuración ---
API_BASE_URL = "http://localhost:5000"

# --- Funciones de la API ---
def get_api_health():
    """Verificar el estado de la API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"❌ Error conectando a la API: {e}")
        return None

def get_buffer_size():
    """Obtener el tamaño de los buffers desde la API"""
    try:
        response = requests.get(f"{API_BASE_URL}/buffer-size", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"transactions_buffer_size": 0, "alerts_buffer_size": 0}
    except Exception as e:
        print(f"❌ Error obteniendo tamaño del buffer: {e}")
        return {"transactions_buffer_size": 0, "alerts_buffer_size": 0}

def get_data_from_api():
    """Obtener datos del buffer desde la API"""
    try:
        response = requests.get(f"{API_BASE_URL}/data", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result["success"] and result["data"]:
                print(f"📥 Recibidos {result['count']} elementos desde la API")
                return result["data"]
        return []
    except Exception as e:
        print(f"❌ Error obteniendo datos de la API: {e}")
        return []

def get_alerts_from_api():
    """Obtener alertas del buffer desde la API"""
    try:
        response = requests.get(f"{API_BASE_URL}/alerts", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result["success"] and result["alerts"]:
                print(f"🚨 Recibidas {result['count']} alertas desde la API")
                return result["alerts"]
        return []
    except Exception as e:
        print(f"❌ Error obteniendo alertas de la API: {e}")
        return []

#Inicia states de streamlit
if "transactions_df" not in st.session_state:
    st.session_state.transactions_df = pd.DataFrame(columns=[
        "userId", "amount", "timestamp", "latitude", "longitude", "ipAddress"
    ])
    print("DataFrame inicializado en session_state.")

if "alerts_df" not in st.session_state:
    st.session_state.alerts_df = pd.DataFrame(columns=[
        "userId", "eventCount", "anomalies", "detectionTime", "windowStart", "windowEnd"
    ])
    print("🚨 DataFrame de alertas inicializado en session_state.")

if "last_update_time" not in st.session_state:
    st.session_state.last_update_time = 0

# --- UI de Streamlit ---

st.set_page_config(layout="wide")
st.title("📊 Dashboard en Tiempo Real: Transacciones y Alertas")


# Botón de actualización manual
if st.button("🔄 Actualizar Datos"):
    st.session_state.last_update_time = 0  # Forzar actualización

# --- Control del filtro de usuario ---
def update_user_filter_callback():
    st.session_state.selected_user_filter = st.session_state.user_filter_widget_key

# Obtener lista de usuarios únicos
actual_users = st.session_state.transactions_df["userId"].unique().tolist()
display_options = ["Todos los usuarios"] + actual_users if actual_users else ["Esperando datos de usuarios..."]

# Lógica para el valor preseleccionado del filtro
default_index = 0
if "selected_user_filter" not in st.session_state:
    st.session_state.selected_user_filter = "Todos los usuarios" if actual_users else display_options[0]
else:
    if st.session_state.selected_user_filter == "Esperando datos de usuarios..." and actual_users:
        st.session_state.selected_user_filter = "Todos los usuarios"
    elif st.session_state.selected_user_filter not in display_options and actual_users:
        st.session_state.selected_user_filter = "Todos los usuarios"

try:
    default_index = display_options.index(st.session_state.selected_user_filter)
except ValueError:
    default_index = 0
    if display_options:
        st.session_state.selected_user_filter = display_options[0]

# Widget de selección de usuario
selected_user_filter = st.selectbox(
    "Filtrar por usuario",
    options=display_options,
    index=default_index,
    key="user_filter_widget_key",
    on_change=update_user_filter_callback
)

st.session_state.selected_user_filter = selected_user_filter

#Tiempo de actualización de los datos
current_time = time.time()
time_since_last_update = current_time - st.session_state.last_update_time

# Solo actualizar si han pasado 5 segundos o es la primera vez o se presionó el botón
if time_since_last_update >= 5 or st.session_state.last_update_time == 0:
    #Obtener datos de la API
    new_data = get_data_from_api()
    new_alerts = get_alerts_from_api()
    
    if new_data:
        print(f"**Procesando {len(new_data)} nuevos mensajes de la API.")
        
        df_new = pd.DataFrame(new_data)
        
        # Convertir timestamp de string a datetime
        df_new['timestamp'] = pd.to_datetime(df_new['timestamp'])
        
        print(f"-DataFrame nuevo creado con {len(df_new)} filas")
        print(f"-Columnas del DataFrame nuevo: {df_new.columns.tolist()}")
        print(f"-Primeras filas del DataFrame nuevo:\n{df_new.head()}")
        
        if not st.session_state.transactions_df.empty and not df_new.empty:
            print(f"Concatenando con DataFrame existente de {len(st.session_state.transactions_df)} filas")
            st.session_state.transactions_df = pd.concat([
                st.session_state.transactions_df,
                df_new
            ], ignore_index=True)
        elif not df_new.empty:
            print(f"! Reemplazando DataFrame vacío con {len(df_new)} filas")
            st.session_state.transactions_df = df_new
        
        # Mantener solo los últimos 50 elementos
        st.session_state.transactions_df = (
            st.session_state.transactions_df
            .sort_values("timestamp", ascending=False)
            .head(100)
            .sort_values("timestamp")
            .reset_index(drop=True)
        )
        print(f"✅ DataFrame actualizado. Total de filas: {len(st.session_state.transactions_df)}")
    else:
        print("⚠️ No hay nuevos datos disponibles en la API")
    
    # Procesar alertas
    if new_alerts:
        print(f"🚨 Procesando {len(new_alerts)} nuevas alertas de la API.")
        
        # Convertir las alertas a DataFrame
        alerts_df_new = pd.DataFrame(new_alerts)
        alerts_df_new['detectionTime'] = pd.to_datetime(alerts_df_new['detectionTime'])
        
        print(f"🚨 DataFrame de alertas nuevo creado con {len(alerts_df_new)} filas")
        
        if not st.session_state.alerts_df.empty and not alerts_df_new.empty:
            print(f"🔄 Concatenando alertas con DataFrame existente de {len(st.session_state.alerts_df)} filas")
            st.session_state.alerts_df = pd.concat([
                st.session_state.alerts_df,
                alerts_df_new
            ], ignore_index=True)
        elif not alerts_df_new.empty:
            print(f"🆕 Reemplazando DataFrame de alertas vacío con {len(alerts_df_new)} filas")
            st.session_state.alerts_df = alerts_df_new
        
        # Mantener solo las últimas 20 alertas
        st.session_state.alerts_df = (
            st.session_state.alerts_df
            .sort_values("detectionTime", ascending=False)
            .head(20)
            .sort_values("detectionTime")
            .reset_index(drop=True)
        )
        print(f"✅ DataFrame de alertas actualizado. Total de filas: {len(st.session_state.alerts_df)}")
    else:
        print("⚠️ No hay nuevas alertas disponibles en la API")
    st.session_state.last_update_time = current_time


# --- Renderizado del dashboard ---
df = st.session_state.transactions_df
alerts_df = st.session_state.alerts_df

# Mostrar información de estado
st.sidebar.info(f"🔄 Última actualización: {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.info(f"📊 Total de transacciones en memoria: {len(df)}")
st.sidebar.info(f"🚨 Total de alertas en memoria: {len(alerts_df)}")

# Obtener tamaños de buffer
buffer_sizes = get_buffer_size()

# Crear pestañas para transacciones y alertas
tab1, tab2 = st.tabs(["📊 Transacciones", "🚨 Alertas"])

with tab1:
    if df.empty:
        st.info("Aún no hay transacciones...")
        st.write("Debug info:")
        st.write(f"API Buffer size: {buffer_sizes['transactions_buffer_size']}")
        st.write(f"Session state keys: {list(st.session_state.keys())}")
    else:
        # Aplicar filtro de usuario
        if st.session_state.selected_user_filter == "Todos los usuarios":
            df_filtered = df.copy()
            filter_title = "Todos los usuarios"
        elif st.session_state.selected_user_filter == "Esperando datos de usuarios...":
            st.info("Esperando datos de usuarios...")
            st.stop()
        else:
            df_filtered = df[df["userId"] == st.session_state.selected_user_filter].copy()
            filter_title = f"Usuario: {st.session_state.selected_user_filter}"
        
        if not df_filtered.empty:
            # Asegurar que timestamp sea datetime y amount sea numérico
            df_filtered['timestamp'] = pd.to_datetime(df_filtered['timestamp'])
            df_filtered['amount'] = pd.to_numeric(df_filtered['amount'], errors='coerce')
            
            # Mostrar estadísticas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Transacciones", len(df_filtered))
            with col2:
                unique_users = df_filtered["userId"].nunique()
                st.metric("Usuarios Únicos", int(unique_users))
            with col3:
                avg_amount = df_filtered['amount'].mean()
                if pd.notna(avg_amount):
                    st.metric("Monto Promedio", f"${avg_amount:.2f}")
                else:
                    st.metric("Monto Promedio", "$0.00")
            
            # Crear gráfico de monto de transacciones por tiempo
            st.subheader(f"📈 Monto de Transacciones por Tiempo - {filter_title}")
            
            # Crear el gráfico según la selección
            if st.session_state.selected_user_filter == "Todos los usuarios":
                # Gráfico con líneas de diferentes colores por usuario
                fig = px.line(
                    df_filtered,
                    x="timestamp",
                    y="amount",
                    color="userId",  # Diferentes colores por usuario
                    markers=True,
                    title=f"Monto de Transacciones por Usuario - {filter_title}",
                    labels={"timestamp": "Tiempo", "amount": "Monto ($)", "userId": "Usuario"}
                )
                fig.update_layout(
                    hovermode="x unified",
                    xaxis_title="Tiempo",
                    yaxis_title="Monto ($)",
                    legend_title="Usuarios"
                )
            else:
                # Gráfico de línea simple para un usuario específico
                fig = px.line(
                    df_filtered,
                    x="timestamp",
                    y="amount",
                    markers=True,
                    title=f"Monto de Transacciones por Tiempo - {filter_title}",
                    labels={"timestamp": "Tiempo", "amount": "Monto ($)", "userId": "Usuario"}
                )
                fig.update_layout(
                    hovermode="x unified",
                    xaxis_title="Tiempo",
                    yaxis_title="Monto ($)"
                )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Mostrar tabla de últimas transacciones
            st.subheader("🧾 Últimas Transacciones")
            display_df = df_filtered[["userId", "amount", "timestamp", "ipAddress"]].copy()
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            display_df["amount"] = display_df["amount"].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "$0.00")
            st.dataframe(display_df.sort_values("timestamp", ascending=False).head(10), use_container_width=True)
            
        else:
            st.warning(f"No hay transacciones para el filtro seleccionado: {st.session_state.selected_user_filter}.")

with tab2:
    if alerts_df.empty:
        st.info("Aún no hay alertas disponibles. Esperando detección de anomalías...")
    else:
        # Mostrar estadísticas de alertas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Alertas", len(alerts_df))
        with col2:
            unique_users_alerts = alerts_df["userId"].nunique()
            st.metric("Usuarios con Alertas", int(unique_users_alerts))
        with col3:
            total_events = alerts_df["eventCount"].sum()
            st.metric("Eventos Analizados", int(total_events))
        
        # Mostrar tabla de alertas
        st.subheader("🚨 Alertas de Anomalías Detectadas")
        
        # Preparar datos para mostrar
        display_alerts_df = alerts_df.copy()
        display_alerts_df["detectionTime"] = display_alerts_df["detectionTime"].dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Convertir la lista de anomalías a string para mostrar
        display_alerts_df["anomalies"] = display_alerts_df["anomalies"].apply(lambda x: "; ".join(x) if isinstance(x, list) else str(x))
        
        # Mostrar las columnas más importantes
        st.dataframe(
            display_alerts_df[["userId", "eventCount", "anomalies", "detectionTime"]].sort_values("detectionTime", ascending=False),
            use_container_width=True
        )
        
        # Mostrar detalles de las últimas alertas
        st.subheader("📋 Detalles de las Últimas Alertas")
        for idx, alert in alerts_df.tail(5).iterrows():
            with st.expander(f"🚨 Alerta para {alert['userId']} - {alert['detectionTime'].strftime('%H:%M:%S')}"):
                st.write(f"**Usuario:** {alert['userId']}")
                st.write(f"**Eventos en ventana:** {alert['eventCount']}")
                st.write(f"**Tiempo de detección:** {alert['detectionTime'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.write("**Anomalías detectadas:**")
                for anomaly in alert['anomalies']:
                    st.write(f"  • {anomaly}")

# Auto-refresh usando st.empty() y time.sleep
placeholder = st.empty()
with placeholder.container():
    st.info("🔄 La página se actualizará automáticamente cada 5 segundos...")
    time.sleep(5)
    st.rerun()