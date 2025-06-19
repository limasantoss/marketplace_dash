# zentsbot_marketplace.py
# 🔧 Cole aqui o conteúdo do bot final do marketplace# 1_🤖_ZentsBot.py

import streamlit as st
import pandas as pd
from datetime import timedelta, date
import re

# --- CONFIGURAÇÃO INICIAL DA PÁGINA ---
st.set_page_config(
    layout="wide", 
    page_title="ZentsBot | Análise Inteligente", 
    page_icon="🤖"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stApp {
            background-color: #0E1117; 
            color: #FAFAFA; 
            font-family: 'Segoe UI', sans-serif;
        }
        .st-emotion-cache-16txtl3 {
            color: #FAFAFA;
        }
    </style>
""", unsafe_allow_html=True)


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

def get_periodo_anterior(data_inicio_atual, data_fim_atual):
    duracao = (data_fim_atual - data_inicio_atual) + timedelta(days=1)
    fim_anterior = data_inicio_atual - timedelta(days=1)
    inicio_anterior = fim_anterior - duracao + timedelta(days=1)
    return inicio_anterior, fim_anterior

def gerar_resposta_analitica(pergunta, df_filtrado, df_total):
    pergunta = pergunta.lower()
    if df_filtrado.empty:
        return "Não encontrei dados para o período selecionado."

    # --- LÓGICA DE ANÁLISE COMPLETA E NA ORDEM CORRETA ---

    # Perguntas mais específicas primeiro para evitar conflitos
    if "concentração" in pergunta or "concentradas" in pergunta:
        faturamento_total = df_filtrado['payment_value'].sum()
        if faturamento_total > 0:
            faturamento_top_10 = df_filtrado.groupby('seller_id')['payment_value'].sum().nlargest(10).sum()
            concentracao = (faturamento_top_10 / faturamento_total)
            insight = ""
            if concentracao > 0.5: insight = "Isso indica uma **alta dependência** dos seus principais vendedores, o que pode ser um risco."
            elif concentracao < 0.2: insight = "Isso mostra um ecossistema **bem diversificado e saudável**, com baixo risco de dependência."
            else: insight = "A concentração está em um nível moderado."
            return (f"📊 As 10 maiores lojas representam **{concentracao:.1%}** do faturamento total. {insight}")
        else: return "Não há faturamento no período para calcular a concentração."

    elif "desempenho dos vendedores" in pergunta or "performance das lojas" in pergunta:
        total_vendedores = df_filtrado['seller_id'].nunique()
        if total_vendedores > 0:
            seller_stats = df_filtrado.groupby('seller_id').agg(pedidos=('order_id', 'count'), nota_media=('review_score', 'mean'))
            alta_performance = seller_stats[(seller_stats['pedidos'] > 10) & (seller_stats['nota_media'] >= 4.5)].shape[0]
            em_risco = seller_stats[(seller_stats['pedidos'] < 5) & (seller_stats['nota_media'] < 3.5)].shape[0]
            intermediarias = total_vendedores - alta_performance - em_risco
            return (f"📈 Analisando **{total_vendedores}** vendedores ativos no período:\n- **Alta Performance:** {alta_performance} lojas.\n- **Intermediárias:** {intermediarias} lojas.\n- **Em Risco:** {em_risco} lojas.")
        else: return "Não há dados de lojas para analisar neste período."

    elif "atrasadas" in pergunta and "avaliações ruins" in pergunta:
        df_com_atraso = df_filtrado[df_filtrado['tempo_entrega'] > 25]
        df_sem_atraso = df_filtrado[df_filtrado['tempo_entrega'] <= 25]
        if not df_com_atraso.empty and not df_sem_atraso.empty:
            nota_com_atraso = df_com_atraso['review_score'].mean()
            nota_sem_atraso = df_sem_atraso['review_score'].mean()
            if nota_com_atraso < nota_sem_atraso:
                return (f"📉 **Sim, há uma correlação.** A nota média para entregas com atraso é **{nota_com_atraso:.2f} estrelas**, "
                        f"enquanto para entregas no prazo é **{nota_sem_atraso:.2f} estrelas**.")
            else: return "✅ **Não parece haver uma correlação clara** entre atrasos e notas ruins no período."
        else: return "✅ Não há dados suficientes de entregas com e sem atraso para comparar no período."

    elif "melhor dia" in pergunta and "vendas" in pergunta:
        vendas_por_dia = df_filtrado.groupby(df_filtrado['order_purchase_timestamp'].dt.date)['payment_value'].sum()
        if not vendas_por_dia.empty:
            melhor_dia = vendas_por_dia.idxmax()
            valor_melhor_dia = vendas_por_dia.max()
            return f"🚀 O melhor dia de vendas foi **{melhor_dia.strftime('%d/%m/%Y')}**, faturando **R$ {valor_melhor_dia:,.2f}**."
        else: return "Não há vendas no período para analisar o melhor dia."

    elif "pior dia" in pergunta and "vendas" in pergunta:
        vendas_por_dia = df_filtrado.groupby(df_filtrado['order_purchase_timestamp'].dt.date)['payment_value'].sum()
        if not vendas_por_dia.empty:
            pior_dia = vendas_por_dia.idxmin()
            valor_pior_dia = vendas_por_dia.min()
            return f"🔧 O pior dia de vendas foi **{pior_dia.strftime('%d/%m/%Y')}**, faturando **R$ {valor_pior_dia:,.2f}**."
        else: return "Não há vendas no período para analisar o pior dia."
    
    elif "loja com mais pedidos" in pergunta:
        total_pedidos_periodo = len(df_filtrado)
        if total_pedidos_periodo > 0:
            loja_top_serie = df_filtrado["seller_id"].value_counts()
            loja_top_id = loja_top_serie.idxmax()
            pedidos_loja_top = loja_top_serie.max()
            percentual_do_total = (pedidos_loja_top / total_pedidos_periodo) * 100
            return (f"🏆 A loja com mais pedidos é a **{loja_top_id}** com **{pedidos_loja_top}** transações, "
                    f"sendo responsável por **{percentual_do_total:.1f}%** de todos os pedidos no período.")
        else: return "Não houve pedidos no período para analisar."
    
    elif "maior ticket" in pergunta and "loja" in pergunta:
        top_ticket = df_filtrado.groupby("seller_id")["payment_value"].mean().nlargest(1)
        if not top_ticket.empty:
            return f"💰 A loja com o maior ticket médio é a **{top_ticket.index[0]}** (R$ {top_ticket.iloc[0]:.2f})."
        else: return "Não há dados de lojas para analisar."
    
    elif "melhor avaliação" in pergunta and "loja" in pergunta:
        top_avaliacao = df_filtrado.groupby("seller_id")["review_score"].mean().nlargest(1)
        if not top_avaliacao.empty:
            return f"⭐ A loja com a melhor avaliação é a **{top_avaliacao.index[0]}** ({top_avaliacao.iloc[0]:.2f} estrelas)."
        else: return "Não há dados de lojas para analisar."

    elif "pior avaliação" in pergunta and "loja" in pergunta:
        pior_avaliacao = df_filtrado.groupby("seller_id")["review_score"].mean().nsmallest(1)
        if not pior_avaliacao.empty:
            return f"📉 A loja com a pior avaliação é a **{pior_avaliacao.index[0]}** ({pior_avaliacao.iloc[0]:.2f} estrelas)."
        else: return "Não há dados de lojas para analisar."

    elif "lojas ativas" in pergunta:
        return f"🏬 Existem **{df_filtrado['seller_id'].nunique()}** lojas ativas no período."

    elif "lojas em risco" in pergunta or "risco" in pergunta and "loja" in pergunta :
        lojas_risco = df_filtrado.groupby("seller_id").agg({"order_id": "count", "review_score": "mean"}).reset_index()
        lojas_risco = lojas_risco[(lojas_risco["order_id"] > 10) & (lojas_risco["review_score"] < 3.5)] 
        if not lojas_risco.empty:
            return f"🔍 Existem **{len(lojas_risco)} lojas** em risco (com mais de 10 pedidos e avaliação média abaixo de 3.5)."
        else:
            return "✅ Nenhuma loja se enquadra nos critérios de risco no período."

    elif "3 categorias mais vendidas" in pergunta or "top 3 categorias" in pergunta or "quais as 3 categorias" in pergunta:
        top_cat = ", ".join(df_filtrado["product_category_name_english"].value_counts().head(3).index)
        return f"📦 As 3 categorias mais vendidas são: **{top_cat}**."
    
    elif "pior" in pergunta and ("logística" in pergunta or "entrega" in pergunta):
        pior_estado = df_filtrado.groupby('customer_state')['tempo_entrega'].mean().idxmax()
        tempo = df_filtrado.groupby('customer_state')['tempo_entrega'].mean().max()
        return f"🚚 O estado com o **maior tempo de entrega** é **{pior_estado}** ({tempo:.1f} dias)."
    
    elif ("melhor" in pergunta or "rápida" in pergunta or "menor" in pergunta) and ("logística" in pergunta or "entrega" in pergunta):
        melhor_estado = df_filtrado.groupby('customer_state')['tempo_entrega'].mean().idxmin()
        tempo = df_filtrado.groupby('customer_state')['tempo_entrega'].mean().min()
        return f"✅ O estado com o **menor tempo de entrega** é **{melhor_estado}** ({tempo:.1f} dias)."

    elif "queda" in pergunta and "vendas" in pergunta:
        vendas_mes = df_filtrado.groupby("ano_mes").size().reset_index(name="Pedidos")
        if len(vendas_mes) >= 2:
            diff = vendas_mes["Pedidos"].pct_change().iloc[-1]
            if diff < -0.1: return f"📉 **Alerta:** Houve uma queda de **{diff:.1%}** nas vendas no último mês do período."
            else: return f"✅ **Análise:** Nenhuma queda significativa foi detectada. A variação foi de **{diff:+.1%}** no último mês do período."
        else: return "Não há dados suficientes no período para analisar uma queda mensal."

    elif "faturamento" in pergunta or "vendas" in pergunta:
        faturamento_atual = df_filtrado['payment_value'].sum()
        data_inicio_atual = df_filtrado['order_purchase_timestamp'].min().date()
        data_fim_atual = df_filtrado['order_purchase_timestamp'].max().date()
        inicio_anterior, fim_anterior = get_periodo_anterior(data_inicio_atual, data_fim_atual)
        df_anterior = df_total[(df_total['order_purchase_timestamp'].dt.date >= inicio_anterior) & (df_total['order_purchase_timestamp'].dt.date <= fim_anterior)]
        faturamento_anterior = df_anterior['payment_value'].sum()
        resposta = f"O faturamento no período foi de **R$ {faturamento_atual:,.2f}**."
        if faturamento_anterior > 0:
            variacao = ((faturamento_atual - faturamento_anterior) / faturamento_anterior) * 100
            if variacao > 0.1:
                resposta += f" Isso representa uma **alta de {variacao:.1f}%** em relação ao período anterior (R$ {faturamento_anterior:,.2f})."
            elif variacao < -0.1:
                resposta += f" Isso representa uma **queda de {abs(variacao):.1f}%** em relação ao período anterior (R$ {faturamento_anterior:,.2f})."
            else:
                resposta += " O valor se manteve estável em relação ao período anterior."
        return resposta

    elif "ticket médio" in pergunta:
        ticket_atual = df_filtrado['payment_value'].mean()
        data_inicio_atual = df_filtrado['order_purchase_timestamp'].min().date()
        data_fim_atual = df_filtrado['order_purchase_timestamp'].max().date()
        inicio_anterior, fim_anterior = get_periodo_anterior(data_inicio_atual, data_fim_atual)
        df_anterior = df_total[(df_total['order_purchase_timestamp'].dt.date >= inicio_anterior) & (df_total['order_purchase_timestamp'].dt.date <= fim_anterior)]
        ticket_anterior = df_anterior['payment_value'].mean() if not df_anterior.empty else 0
        resposta = f"💰 O ticket médio no período foi de **R$ {ticket_atual:.2f}**."
        if ticket_anterior > 0:
            variacao = ((ticket_atual - ticket_anterior) / ticket_anterior) * 100
            if variacao > 0.1:
                resposta += f" Isso é **{variacao:.1f}% maior** que o ticket médio do período anterior (R$ {ticket_anterior:.2f})."
            elif variacao < -0.1:
                resposta += f" Isso é **{abs(variacao):.1f}% menor** que o ticket médio do período anterior (R$ {ticket_anterior:.2f})."
            else:
                resposta += " O valor se manteve estável em relação ao período anterior."
        return resposta
    
    else:
        resposta_padrao = """
        ❓ Desculpe, não entendi. Que tal tentar uma destas perguntas?

        *(Lembre-se que a análise será feita no período que você selecionou no Dashboard!)*

        ---
        **Visão Geral do Negócio**
        - `Qual o faturamento?`
        - `Qual o ticket médio?`
        - `Qual a concentração de vendas?`
        - `Qual foi o melhor dia de vendas?`
        - `Quais as 3 categorias mais vendidas?`

        **Análise de Lojas (Sellers)**
        - `Como está o desempenho dos vendedores?`
        - `Qual a loja com mais pedidos?`
        - `Qual loja tem a melhor avaliação?`
        - `Quais lojas estão em risco?`

        **Análise de Clientes e Logística**
        - `Atrasos na entrega afetam as avaliações?`
        - `Qual estado tem a entrega mais rápida?`
        """
        return resposta_padrao


# --- LÓGICA DA PÁGINA DO BOT ---

st.title("🤖 ZentsBot")
st.markdown(" Faça uma pergunta ou vá para o Dashboard para filtrar um período específico.")

try:
    df_principal = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "date_range" not in st.session_state:
    data_min = df_principal["order_purchase_timestamp"].min().date()
    data_max = df_principal["order_purchase_timestamp"].max().date()
    st.session_state.date_range = (data_min, data_max)

start_date, end_date = st.session_state.date_range
st.info(f"**Período em análise:** {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}. "
        f"Ajuste na página 'Dashboard' no menu ao lado.", icon="📅")

df_contexto = df_principal[
    (df_principal["order_purchase_timestamp"].dt.date >= start_date) &
    (df_principal["order_purchase_timestamp"].dt.date <= end_date)
]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("O que você gostaria de saber sobre este período?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Analisando e comparando dados..."):
            resposta = gerar_resposta_analitica(prompt, df_contexto, df_principal)
            st.markdown(resposta)
    st.session_state.messages.append({"role": "assistant", "content": resposta})
    st.rerun()