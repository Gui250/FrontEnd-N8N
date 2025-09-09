import streamlit as st
import requests
import time

# URL do webhook de produção do n8n
WEBHOOK_URL = "https://projeto01-n8n.peitvn.easypanel.host/webhook/b877c4b1-4eb2-475f-aead-117d6d89614c"

st.set_page_config(page_title="Controle n8n", page_icon="⚙️", layout="centered")
st.title("Controle do Webhook n8n")

# Estado inicial
if "ativo" not in st.session_state:
    st.session_state["ativo"] = False
if "contador" not in st.session_state:
    st.session_state["contador"] = 0
if "ultimo_envio" not in st.session_state:
    st.session_state["ultimo_envio"] = None

# Função para executar um ciclo
def enviar_ciclo():
    payload = {"timestamp": time.time(), "contador": st.session_state["contador"] + 1}
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if r.status_code == 200:
            st.session_state["contador"] += 1
            st.session_state["ultimo_envio"] = time.strftime("%H:%M:%S")
        else:
            st.error(f"Erro {r.status_code}: {r.text[:100]}")
    except Exception as e:
        st.error(f"Falha ao enviar: {e}")

# Botões de controle
col1, col2 = st.columns(2)
with col1:
    if st.button("▶ Iniciar Fluxo"):
        st.session_state["ativo"] = True
        st.success("Loop iniciado!")

with col2:
    if st.button("⏹ Parar Fluxo"):
        st.session_state["ativo"] = False
        st.info("Loop parado!")

# Executar o loop se ativo
if st.session_state["ativo"]:
    enviar_ciclo()
    st.info(f"Loop rodando... total de {st.session_state['contador']} ciclos")
    if st.session_state["ultimo_envio"]:
        st.caption(f"Último envio às {st.session_state['ultimo_envio']}")
    time.sleep(5)  # intervalo de 5s entre chamadas
    st.rerun()
else:
    st.warning("Fluxo parado. Clique em ▶ Iniciar Fluxo para começar.")
