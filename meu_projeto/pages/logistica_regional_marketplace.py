# logistica_regional_marketplace.py
# 🔧 Cole aqui o conteúdo de logística por região do marketplace
import streamlit as st
import pandas as pd

st.set_page_config(page_title="📦 Logística por Região", layout="wide")

@st.cache_data
def carregar_dados_vendedor():
    df = pd.read_csv(
        "../data/processed/dataset_olist_final_limpo.csv",
        parse_dates=["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]
    )
    return df

st.title("📦 Logística por Região")

# Filtro de região
regiao = st.selectbox("Escolha a região:", ["Norte", "Nordeste", "Ambas"])

estados = {
    "Norte": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
    "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
    "Ambas": ["AC", "AP", "AM", "PA", "RO", "RR", "TO", "AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]
}

# Carregar dados
df_total = carregar_dados_vendedor()
df_filtrado = df_total[df_total["customer_state"].isin(estados[regiao])].copy()

# Tempo de entrega
df_filtrado["tempo_entrega"] = (
    df_filtrado["order_delivered_customer_date"] - df_filtrado["order_purchase_timestamp"]
).dt.days

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("⏱️ Tempo médio de entrega", f"{df_filtrado['tempo_entrega'].mean():.1f} dias")
col2.metric("🚚 Frete médio", f"R$ {df_filtrado['freight_value'].mean():.2f}")
col3.metric("📦 Total de pedidos", len(df_filtrado))

# Gráficos
st.markdown(f"### Pedidos por Estado – {regiao}")
st.bar_chart(df_filtrado["customer_state"].value_counts())

st.markdown(f"### Frete Médio por Estado – {regiao}")
frete_estado = df_filtrado.groupby("customer_state")["freight_value"].mean().sort_values()
st.bar_chart(frete_estado)

# Atrasos
st.markdown("### Percentual de Entregas com Atraso")
df_filtrado["atraso"] = df_filtrado["order_delivered_customer_date"] > df_filtrado["order_estimated_delivery_date"]
pct_atraso = df_filtrado["atraso"].mean() * 100
st.write(f"🔴 {pct_atraso:.1f}% dos pedidos foram entregues com atraso.")
