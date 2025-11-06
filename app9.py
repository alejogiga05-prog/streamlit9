import streamlit as st
import pandas as pd
import plotly.express as px
from influxdb_client import InfluxDBClient
from datetime import datetime, timedelta

st.set_page_config(page_title="Dashboard Industrial", layout="wide")

# ======================================
# 🔒 Parámetros de conexión desde secrets
# ======================================
INFLUXDB_URL = st.secrets["INFLUXDB_URL"]
INFLUXDB_TOKEN = st.secrets["INFLUXDB_TOKEN"]
INFLUXDB_ORG = st.secrets["INFLUXDB_ORG"]
INFLUXDB_BUCKET = st.secrets["INFLUXDB_BUCKET"]

# ================ FUNCIONES ================

@st.cache_data(ttl=300)  # cache de 5 minutos
def query_data(measurement, fields, start_date, end_date):
    """Consulta datos desde InfluxDB y retorna un DataFrame pivotado."""
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()

        fields_filter = " or ".join([f'r._field == "{f}"' for f in fields])

        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
          |> range(start: {start_date}, stop: {end_date})
          |> filter(fn: (r) => r._measurement == "{measurement}")
          |> filter(fn: (r) => {fields_filter})
          |> yield(name: "mean")
        '''

        tables = query_api.query(org=INFLUXDB_ORG, query=query)
        data = [(record.get_time(), record.get_field(), record.get_value())
                for table in tables for record in table.records]

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=["time", "field", "value"])
        df = df.pivot(index="time", columns="field", values="value").reset_index()

        return df

    except Exception as e:
        st.error(f"⚠ Error consultando InfluxDB: {e}")
        return pd.DataFrame()


# =
