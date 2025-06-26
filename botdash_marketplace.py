import streamlit as st
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from streamlit_js_eval import streamlit_js_eval
import re


st.set_page_config(
    page_title="Marketplace Bot", 
    page_icon="icone.jpeg",  # troque se quiser outro favicon
    layout="centered"
)


st.markdown("""
    <style>
        h1, h2, h3 { color: #FF6F17; }
        div[data-testid="stMetricLabel"] { color: #FF6F17; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #FF6F17;'>🤖 Marketplace Bot</h1>", unsafe_allow_html=True)

# --- LÓGICA DE DETECÇÃO DE TELA E CARREGAMENTO DE DADOS ---
screen_width = streamlit_js_eval(js_expressions='window.innerWidth', key='SCR_WIDTH') or 769
is_mobile = screen_width < 768

@st.cache_data
def carregar_dados():
    df = pd.read_csv("dataset_olist_final_limpo.csv", parse_dates=["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"])
    df["tempo_entrega"] = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"]).dt.days
    df["dia_da_semana"] = df["order_purchase_timestamp"].dt.day_name()
    return df

def get_periodo_anterior(data_inicio_atual, data_fim_atual):
    duracao = (data_fim_atual - data_inicio_atual)
    fim_anterior = data_inicio_atual - timedelta(days=1)
    inicio_anterior = fim_anterior - duracao
    return inicio_anterior, fim_anterior

def gerar_resposta_analitica(pergunta, df_filtrado, df_total):
    pergunta = pergunta.lower()
    if df_filtrado.empty:
        return "Não encontrei dados para o período selecionado."

    if "concentração de vendas" in pergunta:
        faturamento_total = df_filtrado['payment_value'].sum()
        if faturamento_total > 0:
            faturamento_top_10 = df_filtrado.groupby('seller_id')['payment_value'].sum().nlargest(10).sum()
            concentracao = (faturamento_top_10 / faturamento_total)
            insight = "Isso indica uma alta dependência dos seus principais vendedores." if concentracao > 0.5 else "Isso mostra um ecossistema bem diversificado e saudável."
            return f"📊 As 10 maiores lojas representam **{concentracao:.1%}** do faturamento total. {insight}"
        else:
            return "Não há faturamento no período para calcular a concentração."
    
    elif "desempenho dos vendedores" in pergunta:
        total_vendedores = df_filtrado['seller_id'].nunique()
        if total_vendedores > 0:
            seller_stats = df_filtrado.groupby('seller_id').agg(pedidos=('order_id', 'count'), nota_media=('review_score', 'mean'))
            alta_performance = seller_stats[(seller_stats['pedidos'] > 10) & (seller_stats['nota_media'] >= 4.5)].shape[0]
            em_risco = seller_stats[(seller_stats['pedidos'] < 5) & (seller_stats['nota_media'] < 3.5)].shape[0]
            return f"📈 Analisando **{total_vendedores}** vendedores:\n- **Alta Performance:** {alta_performance}\n- **Em Risco:** {em_risco}"
        else:
            return "Não há dados de lojas para analisar."

    elif "atrasos afetam avaliações" in pergunta:
        df_com_atraso = df_filtrado[df_filtrado['tempo_entrega'] > 25]
        df_sem_atraso = df_filtrado[df_filtrado['tempo_entrega'] <= 25]
        if not df_com_atraso.empty and not df_sem_atraso.empty:
            nota_com_atraso = df_com_atraso['review_score'].mean()
            nota_sem_atraso = df_sem_atraso['review_score'].mean()
            return f"📉 Sim, a nota média para entregas com atraso é **{nota_com_atraso:.2f}**, enquanto para entregas no prazo é **{nota_sem_atraso:.2f}**."
        else:
            return "✅ Não há dados suficientes para comparar."
    
    elif "loja com mais pedidos" in pergunta:
        if not df_filtrado.empty:
            loja_top_id = df_filtrado["seller_id"].value_counts().idxmax()
            return f"🏆 A loja com mais pedidos é a **{loja_top_id}**."
        else:
            return "Não houve pedidos no período para analisar."
    
    else:
        return """
        🤖 Desculpe, não entendi. Tente uma das perguntas abaixo:

        * `Qual a concentração de vendas?` 
        * `Como está o desempenho dos vendedores?`
        * `Atrasos afetam avaliações?`
        * `Qual a loja com mais pedidos?`
        """
# caso o bot de conflito nas respostas coloque as aspas entre a palavra , blz:)
try:
    df_total = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

st.markdown("---")
st.markdown("<h3 style='color: #FF6F17;'>Selecione o Período para Análise</h3>", unsafe_allow_html=True)

anos_disponiveis = sorted(df_total['order_purchase_timestamp'].dt.year.unique(), reverse=True)
meses_map_selectbox = {m:n for m,n in enumerate(['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'],1)}
opcoes_mes = ["Ano Inteiro"] + list(meses_map_selectbox.values())
col1, col2 = st.columns(2)
ano_selecionado = col1.selectbox("Ano:", options=anos_disponiveis)
mes_selecionado_nome = col2.selectbox("Mês:", options=opcoes_mes)

if mes_selecionado_nome == "Ano Inteiro":
    start_date, end_date = date(ano_selecionado, 1, 1), date(ano_selecionado, 12, 31)
else:
    mes_num = list(meses_map_selectbox.keys())[list(meses_map_selectbox.values()).index(mes_selecionado_nome)]
    start_date = date(ano_selecionado, mes_num, 1)
    end_date = start_date + relativedelta(months=1) - relativedelta(days=1)

df_contexto = df_total[(df_total["order_purchase_timestamp"].dt.date >= start_date) & (df_total["order_purchase_timestamp"].dt.date <= end_date)]
st.info(f"Contexto de análise: **{start_date.strftime('%d/%m/%Y')}** a **{end_date.strftime('%d/%m/%Y')}**", icon="📅")
st.markdown("---")

PREGUNTAS_RAPIDAS = [
    "Qual a concentração de vendas?",
    "Como está o desempenho dos vendedores?",
    "Atrasos afetam avaliações?",
    "Qual a loja com mais pedidos?"
]

def set_pergunta(pergunta):
    st.session_state.pergunta_atual = pergunta
if 'pergunta_atual' not in st.session_state:
    st.session_state.pergunta_atual = ""

if is_mobile:
    st.markdown("<h3 style='color: #FF6F17;'>Análises Rápidas</h3>", unsafe_allow_html=True)
    cols = st.columns(2)
    for i, pergunta_rapida in enumerate(PREGUNTAS_RAPIDAS):
        col_atual = cols[i % 2]
        col_atual.button(pergunta_rapida, on_click=set_pergunta, args=(pergunta_rapida,), use_container_width=True)

pergunta = st.text_input("Faça uma pergunta sobre os dados do marketplace:", key="pergunta_atual")

if pergunta:
    with st.spinner("Analisando dados do marketplace..."):
        resposta = gerar_resposta_analitica(pergunta, df_contexto, df_total)
        st.success(resposta)
