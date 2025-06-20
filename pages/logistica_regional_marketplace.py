import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="📦 Logística N/NE", layout="wide", page_icon="icone.jpeg")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
        /* Regra para colorir todos os títulos e subtítulos */
        h1, h2, h3 {
            color: #FF6F17;
        }
        /* Regra para colorir os rótulos dos indicadores (KPIs) */
        div[data-testid="stMetricLabel"] {
            color: #FF6F17;
        }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def carregar_dados():
    df = pd.read_csv(
        "dataset_olist_final_limpo.csv",
        parse_dates=["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]
    )
    df["tempo_entrega"] = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"]).dt.days
    df["atraso"] = df["order_delivered_customer_date"] > df["order_estimated_delivery_date"]
    return df

st.title("📦 Logística Detalhada: Regiões Norte e Nordeste")

try:
    df_total = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

# --- SINCRONIZAÇÃO COM FILTRO DE DATA GLOBAL ---
if 'date_range' in st.session_state:
    start_date, end_date = st.session_state.date_range
    df_filtrado_data = df_total[
        (df_total["order_purchase_timestamp"].dt.date >= start_date) &
        (df_total["order_purchase_timestamp"].dt.date <= end_date)
    ]
else:
    st.warning("Nenhum período selecionado no Dashboard. Analisando o período completo.")
    start_date = df_total["order_purchase_timestamp"].min().date()
    end_date = df_total["order_purchase_timestamp"].max().date()
    df_filtrado_data = df_total

st.markdown("---")


estados_norte_nordeste = ["AC", "AP", "AM", "PA", "RO", "RR", "TO", "AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]
df_filtrado_regiao = df_filtrado_data[df_filtrado_data["customer_state"].isin(estados_norte_nordeste)].copy()

if not df_filtrado_regiao.empty:
    st.subheader("Filtre por Cidade ")
    cidades_disponiveis = sorted(df_filtrado_regiao['customer_city'].unique())
    cidades_selecionadas = st.multiselect(
        "Selecione uma ou mais cidades para detalhar a análise:",
        options=cidades_disponiveis,
        placeholder="Deixe em branco para ver todas as cidades das regiões N/NE"
    )

    if cidades_selecionadas:
        df_filtrado = df_filtrado_regiao[df_filtrado_regiao['customer_city'].isin(cidades_selecionadas)].copy()
    else:
        df_filtrado = df_filtrado_regiao
else:
    df_filtrado = df_filtrado_regiao
    cidades_selecionadas = []


# --- EXIBIÇÃO DA PÁGINA ---
cidades_info = ", ".join(cidades_selecionadas) if cidades_selecionadas else "Todas as cidades"
st.info(f"Analisando de **{start_date.strftime('%d/%m/%Y')}** a **{end_date.strftime('%d/%m/%Y')}** | Regiões: **Norte e Nordeste** | Cidades: **{cidades_info}**.", icon="🗺️")

if df_filtrado.empty:
    st.warning("Não há dados para os filtros selecionados.")
    st.stop()

st.markdown("---")

# KPIs
st.subheader(f"Indicadores para a Seleção")
col1, col2, col3 = st.columns(3)
col1.metric("⏱️ Tempo médio de entrega", f"{df_filtrado['tempo_entrega'].mean():.1f} dias")
col2.metric("🚚 Frete médio", f"R$ {df_filtrado['freight_value'].mean():.2f}")
pct_atraso = df_filtrado["atraso"].mean() * 100
col3.metric("🔴 Pedidos com Atraso", f"{pct_atraso:.1f}%")

st.markdown("---")

# Gráficos com Plotly
st.subheader(f"Análise por Estado")
col_graf1, col_graf2 = st.columns(2)
with col_graf1:
    pedidos_estado = df_filtrado["customer_state"].value_counts().reset_index()
    pedidos_estado.columns = ["Estado", "Pedidos"]
    fig1 = px.bar(pedidos_estado, x="Pedidos", y="Estado", orientation='h', title="Total de Pedidos por Estado")
    fig1.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig1, use_container_width=True)

with col_graf2:
    frete_estado = df_filtrado.groupby("customer_state")["freight_value"].mean().sort_values().reset_index()
    frete_estado.columns = ["Estado", "Frete Médio"]
    fig2 = px.bar(frete_estado, x="Frete Médio", y="Estado", orientation='h', title="Frete Médio por Estado")
    fig2.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Valor (R$)")
    st.plotly_chart(fig2, use_container_width=True)