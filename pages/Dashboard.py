import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="Envio Leads - Dashboard", page_icon="📊")

st.title("Dashboard de Leads")

st.markdown(
    """
    <style>
    .card {background: #ffffff; border: 1px solid #eee; border-radius: 14px; padding: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.04);}    
    </style>
    """,
    unsafe_allow_html=True,
)
st.caption("Carregue um arquivo para visualizar estatísticas e gráficos.")

st.markdown("<div class='card'>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Escolha um arquivo Excel ou CSV", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.subheader("Gráfico de Barras - Exemplo")
        if not df.empty and len(df.columns) >= 2:
            fig, ax = plt.subplots()
            df.set_index(df.columns[0]).iloc[:20].plot(kind='bar', ax=ax)
            st.pyplot(fig)
        else:
            st.warning("O arquivo não tem colunas suficientes para o gráfico de exemplo.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
else:
    st.info("Nenhum arquivo carregado ainda.")

st.markdown("</div>", unsafe_allow_html=True)
