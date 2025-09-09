import streamlit as st
import requests
import time
import json
from requests.exceptions import ReadTimeout
import random
import re

# Configurações principais
WEBHOOK_MAIN_URL = "https://projeto01-n8n.peitvn.easypanel.host/webhook/b877c4b1-4eb2-475f-aead-117d6d89614c"
WORKFLOW_ID = "D2c8LMH4Fq8JT6CQ"

st.set_page_config(layout="wide", page_title="Controle n8n Loop", page_icon="⚙️")
st.title("🔄 Controle do Fluxo n8n - Loop Inteligente")

# --- Inicialização do Estado ---
def init_session_state():
    defaults = {
        "status": "Parado",
        "loop_active": False,
        "loop_count": 0,
        "execution_start_time": None,
        "last_loop_execution": 0,
        "loop_delay": 10,
        "message_history": {},
        "leads_numbers": [],
        "current_number_index": 0,
        "number_generation_mode": "real_leads",
        "webhook_url": WEBHOOK_MAIN_URL,
        "net_logs": []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Funções Utilitárias ---
# Funções de controle de números removidas - n8n gerencia os leads

# Funções de números removidas - n8n fará a leitura dos leads

def call_webhook(url, payload=None, timeout=30):
    """Chama o webhook com o payload."""
    try:
        response = requests.post(url, json=(payload or {}), timeout=timeout)
        
        # Log da tentativa
        st.session_state["net_logs"].append({
            "when": time.strftime("%H:%M:%S"),
            "action": "POST",
            "status": response.status_code,
            "payload": payload
        })
        
        return response
    except Exception as e:
        st.session_state["net_logs"].append({
            "when": time.strftime("%H:%M:%S"),
            "action": "ERROR",
            "error": str(e)
        })
        raise e

def execute_workflow_run():
    """Executa uma rodada completa do workflow e aguarda finalização."""
    try:
        if st.session_state.get("loop_stop_flag", False):
            return False
        
        # Payload simples - apenas trigger para o workflow
        payload = {
            "timestamp": time.time(),
            "trigger": "start_workflow",
            "execution_id": st.session_state.get("loop_count", 0) + 1
        }
        
        # Log do início da execução
        st.session_state["net_logs"].append({
            "when": time.strftime("%H:%M:%S"),
            "action": "STARTING_WORKFLOW",
            "execution": payload["execution_id"]
        })
        
        # Chamar webhook para iniciar workflow
        response = call_webhook(st.session_state["webhook_url"], payload, timeout=60)
        
        # Incrementar contador de execuções
        st.session_state["loop_count"] += 1
        
        if response.status_code == 200:
            # Workflow iniciado com sucesso
            st.session_state["net_logs"].append({
                "when": time.strftime("%H:%M:%S"),
                "action": "WORKFLOW_COMPLETED",
                "execution": payload["execution_id"],
                "status": response.status_code,
                "response_time": "OK"
            })
            return True
        else:
            # Log de erro mas continua
            st.session_state["net_logs"].append({
                "when": time.strftime("%H:%M:%S"),
                "action": "WORKFLOW_ERROR",
                "execution": payload["execution_id"],
                "status": response.status_code,
                "error": response.text[:200]
            })
            return True  # Continuar mesmo com erro
            
    except Exception as e:
        # Log de exceção mas continua
        st.session_state["net_logs"].append({
            "when": time.strftime("%H:%M:%S"),
            "action": "EXECUTION_EXCEPTION",
            "error": str(e)
        })
        return True

# --- Interface Principal ---
st.write(f"📌 **Status atual:** {st.session_state['status']}")

# Métricas do loop
if st.session_state.get("loop_active", False):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔄 Status", "ATIVO", delta="Loop executando")
    with col2:
        st.metric("🔄 Execuções", st.session_state.get("loop_count", 0))
    with col3:
        if st.session_state.get("execution_start_time"):
            runtime = time.time() - st.session_state["execution_start_time"]
            st.metric("⏱️ Tempo Ativo", f"{runtime:.0f}s")
        else:
            st.metric("⏱️ Tempo Ativo", "0s")
    with col4:
        # Mostrar próxima execução
        current_time = time.time()
        last_execution = st.session_state.get("last_loop_execution", 0)
        loop_delay = st.session_state.get("loop_delay", 30)
        remaining = max(0, loop_delay - (current_time - last_execution))
        st.metric("⏳ Próxima Em", f"{remaining:.0f}s")
    
    st.success("🟢 **Workflow executando** - n8n processando leads completos")
    
    # Controle de intervalo entre execuções
    col_delay1, col_delay2 = st.columns([1, 2])
    with col_delay1:
        new_delay = st.number_input(
            "Intervalo entre execuções (segundos)", 
            min_value=30, 
            max_value=300, 
            value=st.session_state.get("loop_delay", 60),
            step=30,
            help="Tempo para aguardar entre execuções completas do workflow"
        )
        if new_delay != st.session_state.get("loop_delay"):
            st.session_state["loop_delay"] = new_delay
    with col_delay2:
        current_time = time.time()
        last_execution = st.session_state.get("last_loop_execution", 0)
        remaining = max(0, st.session_state["loop_delay"] - (current_time - last_execution))
        if remaining > 0:
            st.info(f"⏳ Aguardando {remaining:.0f}s para próxima execução completa")
        else:
            st.info("🔄 Executando workflow completo...")

# Botões de controle
st.divider()
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("▶️ Iniciar Fluxo", type="primary", disabled=st.session_state.get("loop_active", False)):
        st.session_state["status"] = "Em Execução"
        st.session_state["loop_active"] = True
        st.session_state["loop_count"] = 0
        st.session_state["execution_start_time"] = time.time()
        st.session_state["last_loop_execution"] = 0
        st.session_state["loop_stop_flag"] = False
        st.success("🚀 Fluxo iniciado! n8n executará workflows completos")
        st.rerun()

with col2:
    if st.button("⏹️ Parar Fluxo", disabled=not st.session_state.get("loop_active", False)):
        st.session_state["loop_active"] = False
        st.session_state["status"] = "Parado"
        st.session_state["loop_stop_flag"] = True
        st.info("🛑 Fluxo parado!")
        st.rerun()

with col3:
    if st.button("🗑️ Limpar Logs"):
        st.session_state["loop_count"] = 0
        st.session_state["net_logs"] = []
        st.success("🗑️ Logs limpos!")
        st.rerun()

# Configurações
with st.expander("⚙️ Configurações", expanded=False):
    st.session_state["webhook_url"] = st.text_input(
        "URL do Webhook n8n",
        value=st.session_state.get("webhook_url", WEBHOOK_MAIN_URL),
        help="URL do webhook que iniciará o workflow completo no n8n"
    )

    # Teste manual
    st.markdown("**🧪 Teste de Conexão:**")
    if st.button("🔥 Testar Webhook", type="primary"):
        test_payload = {
            "timestamp": time.time(),
            "trigger": "test_connection",
            "test": True
        }
        
        try:
            with st.spinner("Testando conexão com n8n..."):
                response = call_webhook(st.session_state["webhook_url"], test_payload, timeout=30)
            
            if response.status_code == 200:
                st.success("✅ **WEBHOOK FUNCIONANDO!** n8n respondeu corretamente")
                st.balloons()
                st.info("🎯 O workflow no n8n deve processar os leads automaticamente")
            else:
                st.error(f"❌ Erro {response.status_code}: {response.text[:100]}")
                st.warning("🔧 Verifique se o workflow está ativo no n8n!")
        except Exception as e:
            st.error(f"❌ Falha na conexão: {e}")
            st.warning("🔧 Verifique se o n8n está online!")
    
    st.info("💡 **Como funciona**: O Python apenas dispara o webhook. O n8n faz toda a leitura e processamento dos leads.")

# Logs recentes e debug
if st.session_state.get("net_logs"):
    with st.expander("📋 Debug - Últimas Operações", expanded=True):
        st.caption("🔍 Acompanhe em tempo real o que está sendo enviado para o n8n:")
        
        # Mostrar últimos 8 logs
        recent_logs = st.session_state["net_logs"][-8:]
        for log in recent_logs:
            if log.get("action") == "STARTING_WORKFLOW":
                st.info(f"🚀 {log['when']} - Iniciando execução #{log.get('execution', '?')} do workflow")
            elif log.get("action") == "WORKFLOW_COMPLETED":
                st.success(f"✅ {log['when']} - Execução #{log.get('execution', '?')} finalizada - Status {log.get('status', '?')}")
            elif log.get("action") == "WORKFLOW_ERROR":
                st.error(f"❌ {log['when']} - Erro na execução #{log.get('execution', '?')} - Status {log.get('status', '?')}")
                if log.get("error"):
                    st.caption(f"Detalhes: {log['error']}")
            elif log.get("action") == "EXECUTION_EXCEPTION":
                st.error(f"🚨 {log['when']} - Exceção na execução: {log.get('error', 'Erro desconhecido')}")
            elif log.get("action") == "POST":
                st.write(f"🔗 {log['when']} - HTTP {log.get('status', '?')} - Trigger enviado")
        
        # Estatísticas rápidas
        if len(recent_logs) > 0:
            success_count = len([l for l in recent_logs if l.get("action") == "WORKFLOW_COMPLETED"])
            error_count = len([l for l in recent_logs if l.get("action") == "WORKFLOW_ERROR"])
            st.caption(f"📊 Últimas execuções: {success_count} sucessos, {error_count} erros")

# Lógica de execução automática - workflow completo
if st.session_state.get("loop_active", False):
    current_time = time.time()
    last_execution = st.session_state.get("last_loop_execution", 0)
    loop_delay = st.session_state.get("loop_delay", 60)  # Padrão 60s entre execuções
    
    if current_time - last_execution >= loop_delay:
        # Executar workflow completo
        continue_execution = execute_workflow_run()
        st.session_state["last_loop_execution"] = current_time
        
        if not continue_execution:
            st.session_state["loop_active"] = False
            st.session_state["status"] = "Parado"
    
    # Auto-refresh mais suave para execuções completas
    time.sleep(2)
    st.rerun()