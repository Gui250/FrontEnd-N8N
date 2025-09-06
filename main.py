import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import time
import json
import base64
from requests.exceptions import ReadTimeout
try:
    from streamlit_lottie import st_lottie
except Exception:
    st_lottie = None



WEBHOOK_MAIN_URL = "https://projeto01-n8n.peitvn.easypanel.host/webhook/ce723d0d-a280-414f-aec3-85c940f7dc6f"



st.set_page_config(layout="wide", page_title="Envio Leads - Controle", page_icon="⚙️")
st.title("Controle do Fluxo n8n")


st.markdown(
    """
    <style>
    .status-badge {padding:6px 10px;border-radius:12px;font-weight:600;background:#eef6ff;color:#175cd3;display:inline-block;}
    .card {background: #ffffff; border: 1px solid #eee; border-radius: 14px; padding: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.04);}
    .small {opacity:0.8;font-size:0.9rem}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Animação de topo ---
def load_lottie(url: str):
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None

hero_cols = st.columns([2,1])
with hero_cols[0]:
    st.markdown("<span class='status-badge'>Painel de Controle</span>", unsafe_allow_html=True)
    st.caption("Gerencie o fluxo, acompanhe esperas e libere próximos leads.")
with hero_cols[1]:
    anim = load_lottie("https://assets2.lottiefiles.com/packages/lf20_kyu7xb1v.json")
    if anim and st_lottie:
        st_lottie(anim, height=120, key="hero")

# --- Estado da Aplicação ---
if "status" not in st.session_state:
    st.session_state["status"] = "Parado"

if "wait_url" not in st.session_state:
    st.session_state["wait_url"] = None

if "current_lead" not in st.session_state:
    st.session_state["current_lead"] = None

st.write(f"📌 Status atual: **{st.session_state['status']}**")

# --- Helper para chamadas a webhooks (POST com fallback para GET quando necessário) ---

def call_webhook(url, payload=None, timeout=30):
    try:
        resp = requests.post(url, json=(payload or {}), timeout=timeout)
        # Se o webhook estiver configurado para GET, o n8n retorna 404 com dica de método
        if resp.status_code == 404 and "Did you mean to make a GET request" in resp.text:
            resp = requests.get(url, params=(payload or {}), timeout=timeout)
        return resp
    except Exception as e:
        raise e

# Exibir a URL de espera gerada, se houver
if st.session_state.get("wait_url"):
    st.markdown(f"**URL do Webhook Wait para o Lead atual:** `{st.session_state['wait_url']}`")
    if st.button("🌐 Liberar Próximo"):
        try:
            with st.spinner("Liberando próximo lead..."):
                response = call_webhook(st.session_state["wait_url"], {"status": "liberado"}, timeout=30)
            if response.status_code == 200:
                st.session_state["status"] = "Liberado"
                st.session_state["wait_url"] = None
                st.success("Fluxo liberado com sucesso! Aguarde o próximo lead.")
                st.rerun()
            else:
                st.error(f"Erro ao liberar fluxo: {response.status_code} - {response.text}")
        except ReadTimeout:
            st.error("Tempo esgotado ao liberar. Configure o Webhook no n8n para responder imediatamente (Response Mode: On Received) ou aumente o timeout.")
        except Exception as e:
            st.error(f"Erro ao tentar liberar o fluxo: {e}")

# --- Funções do Fluxo de Trabalho ---
def iniciar_fluxo():
    """Inicia o fluxo de trabalho do n8n."""
    st.session_state["status"] = "Iniciando..."
    st.info("Iniciando o fluxo. Aguarde...")

    try:
        with st.spinner("Iniciando fluxo no n8n..."):
            response = call_webhook(WEBHOOK_MAIN_URL, {"iniciar": True}, timeout=30)
        if response.status_code == 200:
            st.session_state["status"] = "Em Execução"
            st.success("Fluxo principal iniciado com sucesso!")
        else:
            st.error(f"Erro ao iniciar fluxo: {response.status_code} - {response.text}")
    except ReadTimeout:
        st.error("Tempo esgotado ao iniciar. No n8n, ative resposta imediata no Webhook (On Received) ou aumente o timeout.")
    except Exception as e:
        st.error(f"Erro: {e}")

def parar_fluxo():
    """Interrompe o fluxo de trabalho."""
    st.session_state["status"] = "Parando..."
    try:
        with st.spinner("Parando fluxo no n8n..."):
            response = call_webhook(WEBHOOK_MAIN_URL, {"status": "stopped"}, timeout=30)
        if response.status_code == 200:
            st.session_state["status"] = "Parado"
            st.session_state["wait_url"] = None
            st.warning("Fluxo interrompido com sucesso!")
        else:
            st.error(f"Erro ao interromper fluxo: {response.status_code} - {response.text}")
    except ReadTimeout:
        st.error("Tempo esgotado ao parar. No n8n, ative resposta imediata no Webhook (On Received) ou aumente o timeout.")
    except Exception as e:
        st.error(f"Erro: {e}")

# --- Seção de Controle do App ---
col1, col2 = st.columns(2)

with col1:
    if st.button("▶ Iniciar Fluxo"):
        iniciar_fluxo()

with col2:
    if st.button("◼ Parar Fluxo"):
        parar_fluxo()

st.divider()
st.info("A seção de análise foi movida para a página 'Dashboard' no menu lateral.")