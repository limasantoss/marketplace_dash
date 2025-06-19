# pages/2_📊_Dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta, date

# --- FUNÇÕES DE LÓGICA ---
@st.cache_data
def carregar_dados():
    df = pd.read_csv("../data/processed/dataset_olist_final_limpo.csv", parse_dates=["order_purchase_timestamp", "order_delivered_customer_date"])
    try:
        df['order_purchase_timestamp'] = df['order_purchase_timestamp'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
        df['order_delivered_customer_date'] = df['order_delivered_customer_date'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
    except TypeError:
        df['order_purchase_timestamp'] = df['order_purchase_timestamp'].dt.tz_convert('America/Sao_Paulo')
        df['order_delivered_customer_date'] = df['order_delivered_customer_date'].dt.tz_convert('America/Sao_Paulo')
    df["ano_mes"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df.dropna(subset=['order_delivered_customer_date', 'order_purchase_timestamp'], inplace=True)
    df["tempo_entrega"] = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"]).dt.days
    return df

# --- LÓGICA DA PÁGINA DO DASHBOARD ---

st.set_page_config(layout="wide", page_title="Dashboard Zents", page_icon="📊")
st.title("📊 Dashboard de Análise")

try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()

def atualizar_periodo():
    st.session_state.date_range = st.session_state.filtro_data_slider

data_min_geral = df["order_purchase_timestamp"].min().date()
data_max_geral = df["order_purchase_timestamp"].max().date()

if 'date_range' not in st.session_state:
    st.session_state.date_range = (data_min_geral, data_max_geral)

st.sidebar.header("Filtro de Período Global")
st.sidebar.slider(
    "Selecione o intervalo:", 
    min_value=data_min_geral, 
    max_value=data_max_geral, 
    value=st.session_state.date_range,
    key="filtro_data_slider",
    on_change=atualizar_periodo
)
st.sidebar.markdown("---") 

selecao_dashboard = st.sidebar.radio(
    "Selecione uma seção do Dashboard:",
    ["Visão Geral", "Análise de Lojas", "Análise de Logística"]
)

start_date, end_date = st.session_state.date_range
df_filtrado = df[
    (df["order_purchase_timestamp"].dt.date >= start_date) &
    (df["order_purchase_timestamp"].dt.date <= end_date)
]

st.info(f"Exibindo dados de **{start_date.strftime('%d/%m/%Y')}** a **{end_date.strftime('%d/%m/%Y')}**. "
        f"As perguntas na página do ZentsBot também usarão este período.", icon="✅")
st.markdown("---")

if selecao_dashboard == "Visão Geral":
    st.subheader("📌 Visão Geral do Período Selecionado")
    cols = st.columns(3)
    kpis = [
        ("Pedidos", f'{len(df_filtrado):,}'),
        ("Clientes Únicos", f'{df_filtrado["customer_id"].nunique():,}'),
        ("Ticket Médio (R$)", f"{df_filtrado['payment_value'].mean():.2f}"),
        ("Tempo Médio Entrega", f"{df_filtrado['tempo_entrega'].mean():.1f} dias"),
        ("Lojas Ativas", f'{df_filtrado["seller_id"].nunique():,}'),
        ("Nota Média", f'{df_filtrado["review_score"].mean():.2f}')
    ]
    for i, (k, v) in enumerate(kpis):
        with cols[i % 3]:
            st.metric(label=k, value=v)
    
    st.markdown("---")
    col_graf_1, col_graf_2 = st.columns(2)
    with col_graf_1:
        pedidos_mes = df_filtrado.groupby("ano_mes").size().reset_index(name="Pedidos")
        fig = px.bar(pedidos_mes, x="ano_mes", y="Pedidos", title="Pedidos por Mês")
        st.plotly_chart(fig, use_container_width=True)
    with col_graf_2:
        ticket_medio = df_filtrado.groupby("ano_mes")["payment_value"].mean().reset_index()
        fig2 = px.line(ticket_medio, x="ano_mes", y="payment_value", title="Ticket Médio por Mês")
        st.plotly_chart(fig2, use_container_width=True)
    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        df_cat_filtered = df_filtrado.dropna(subset=['product_category_name_english'])
        top_categorias = df_cat_filtered['product_category_name_english'].value_counts().nlargest(10).reset_index()
        top_categorias.columns = ['Categoria', 'Pedidos']
        fig3 = px.bar(top_categorias, x='Pedidos', y='Categoria', orientation='h', title='Top 10 Categorias Mais Vendidas')
        fig3.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        vendas_por_estado = df_filtrado['customer_state'].value_counts().reset_index()
        vendas_por_estado.columns = ['state_code', 'orders']
        fig4 = px.choropleth(vendas_por_estado,
                             geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
                             locations='state_code',
                             featureidkey="properties.sigla",
                             color='orders',
                             color_continuous_scale="Purples",
                             scope="south america",
                             title="Mapa de Pedidos por Estado")
        fig4.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig4, use_container_width=True)

elif selecao_dashboard == "Análise de Lojas":
    st.subheader("🏬 Análise de Lojas (Sellers) no Período")
    top_lojas = df_filtrado["seller_id"].value_counts().head(10).reset_index()
    top_lojas.columns = ["Loja", "Pedidos"]
    fig = px.bar(top_lojas, x="Pedidos", y="Loja", title="Top 10 Lojas com Mais Pedidos", orientation='h')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        top_ticket = df_filtrado.groupby("seller_id")["payment_value"].mean().nlargest(10).reset_index()
        top_ticket.columns = ["Loja", "Ticket Médio"]
        fig2 = px.bar(top_ticket, x="Ticket Médio", y="Loja", title="Top 10 Lojas por Ticket Médio", orientation='h')
        fig2.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        top_avaliacao = df_filtrado.groupby("seller_id")["review_score"].mean().nlargest(10).reset_index()
        top_avaliacao.columns = ["Loja", "Nota Média"]
        fig3 = px.bar(top_avaliacao, x="Nota Média", y="Loja", title="Top 10 Lojas por Avaliação", orientation='h')
        fig3.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_range=[3.5, 5])
        st.plotly_chart(fig3, use_container_width=True)

elif selecao_dashboard == "Análise de Logística":
    st.subheader("🚚 Análise de Logística no Período")
    col1, col2 = st.columns(2)
    with col1:
        tempo_estado = df_filtrado.groupby("customer_state")["tempo_entrega"].mean().sort_values().reset_index()
        fig = px.bar(tempo_estado, x="tempo_entrega", y="customer_state", title="Tempo Médio de Entrega por Estado", orientation='h')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Tempo Médio (dias)", yaxis_title="Estado")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        nota_estado = df_filtrado.groupby("customer_state")["review_score"].mean().sort_values().reset_index()
        fig2 = px.bar(nota_estado, x="review_score", y="customer_state", title="Nota Média por Estado", orientation='h')
        fig2.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="Nota Média", yaxis_title="Estado")
        st.plotly_chart(fig2, use_container_width=True)

