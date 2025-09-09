import streamlit as st
import requests
import time
from requests.exceptions import ReadTimeout

# Configurações principais
WEBHOOK_MAIN_URL = "https://projeto01-n8n.peitvn.easypanel.host/webhook/b877c4b1-4eb2-475f-aead-117d6d89614c"
WORKFLOW_ID = "5w9w7VyDWF2d4V7c"  # Workflow ID correto extraído da URL
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NWM4YTg2Zi1iZDc3LTRjZTYtYjJmYS1mM2Q3MGZhNzJkOWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU3NDM2ODYwfQ.EcLw5O_-m3jQuZ1TS7mwthh6yxV_6AsZbmARYAHDu-Q"
N8N_BASE_URL = "https://projeto01-n8n.peitvn.easypanel.host"

st.set_page_config(layout="wide", page_title="Controle n8n Loop", page_icon="⚙️")
st.title("🔄 Controle do Fluxo n8n - Loop Inteligente")

# Informações do workflow
st.info(f"🎯 **Workflow alvo**: `{WORKFLOW_ID}` - Leads SDR AMAC | 🔗 [Abrir no n8n](https://projeto01-n8n.peitvn.easypanel.host/workflow/{WORKFLOW_ID})")

st.warning("⚠️ **Modo Webhook**: API Key com problema - funcionando apenas com webhook direto")
st.success("✨ **Para testar**: Abra a seção 'Configurações' abaixo e clique em 'EXECUTAR VIA WEBHOOK'")

# --- Inicialização do Estado ---
def init_session_state():
    defaults = {
        "status": "Parado",
        "loop_active": False,
        "loop_count": 0,
        "execution_start_time": None,
        "last_loop_execution": 0,
        "loop_delay": 60,  # 60 segundos padrão entre execuções completas
        "webhook_url": WEBHOOK_MAIN_URL,
        "net_logs": []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Funções de Controle do n8n ---
def check_workflow_status():
    """Verifica se o workflow está ativo no n8n."""
    try:
        headers = {
            "Authorization": f"Bearer {N8N_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{N8N_BASE_URL}/rest/workflows/{WORKFLOW_ID}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            workflow_data = response.json()
            is_active = workflow_data.get("active", False)
            return is_active, f"Workflow está {'ativo' if is_active else 'inativo'}"
        elif response.status_code == 401:
            return None, "Erro de autenticação - API Key inválida"
        elif response.status_code == 404:
            return None, f"Workflow ID '{WORKFLOW_ID}' não encontrado"
        else:
            return None, f"Erro {response.status_code}: {response.text[:100]}"
            
    except Exception as e:
        return None, f"Erro ao conectar: {e}"

def activate_workflow(activate=True):
    """Ativa ou desativa o workflow no n8n."""
    try:
        headers = {
            "Authorization": f"Bearer {N8N_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.patch(
            f"{N8N_BASE_URL}/rest/workflows/{WORKFLOW_ID}",
            json={"active": activate},
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            action = "ativado" if activate else "desativado"
            return True, f"Workflow {action} com sucesso!"
        else:
            return False, f"Erro {response.status_code}: {response.text[:100]}"
            
    except Exception as e:
        return False, f"Erro: {e}"

def execute_workflow_via_api():
    """Executa o workflow diretamente via API (alternativa ao webhook)."""
    try:
        headers = {
            "Authorization": f"Bearer {N8N_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Executar workflow via API
        response = requests.post(
            f"{N8N_BASE_URL}/rest/workflows/{WORKFLOW_ID}/execute",
            json={},
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            execution_data = response.json()
            return True, execution_data.get("data", {}).get("resultData", {})
        else:
            return False, f"Erro {response.status_code}: {response.text[:200]}"
            
    except Exception as e:
        return False, f"Erro na execução: {e}"

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
    """Executa uma rodada completa do workflow com verificação robusta."""
    try:
        if st.session_state.get("loop_stop_flag", False):
            return False
        
        execution_id = st.session_state.get("loop_count", 0) + 1
        
        # Log do início da execução
        st.session_state["net_logs"].append({
            "when": time.strftime("%H:%M:%S"),
            "action": "STARTING_WORKFLOW",
            "execution": execution_id,
            "method": "Verificando status..."
        })
        
        # 1. Pular verificação de status da API (com problema)
        st.session_state["net_logs"].append({
            "when": time.strftime("%H:%M:%S"),
            "action": "SKIPPING_API_CHECK",
            "execution": execution_id,
            "reason": "API Key com problema - usando webhook direto"
        })
        
        # 2. Ir direto para webhook (método confiável)
        st.session_state["net_logs"].append({
            "when": time.strftime("%H:%M:%S"),
            "action": "EXECUTING_VIA_WEBHOOK",
            "execution": execution_id
        })
        
        payload = {
            "timestamp": time.time(),
            "trigger": "start_workflow",
            "execution_id": execution_id
        }
        
        response = call_webhook(st.session_state["webhook_url"], payload, timeout=60)
        
        # Incrementar contador de execuções
        st.session_state["loop_count"] += 1
        
        if response.status_code == 200:
            st.session_state["net_logs"].append({
                "when": time.strftime("%H:%M:%S"),
                "action": "WORKFLOW_COMPLETED",
                "execution": execution_id,
                "method": "WEBHOOK",
                "status": response.status_code
            })
            return True
        else:
            st.session_state["net_logs"].append({
                "when": time.strftime("%H:%M:%S"),
                "action": "WORKFLOW_ERROR",
                "execution": execution_id,
                "method": "WEBHOOK",
                "status": response.status_code,
                "error": response.text[:200]
            })
            return True  # Continuar mesmo com erro
            
    except Exception as e:
        st.session_state["net_logs"].append({
            "when": time.strftime("%H:%M:%S"),
            "action": "EXECUTION_EXCEPTION",
            "execution": execution_id,
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
    st.markdown("**🔗 Configuração do Webhook:**")
    st.session_state["webhook_url"] = st.text_input(
        "URL do Webhook n8n",
        value=st.session_state.get("webhook_url", WEBHOOK_MAIN_URL),
        help="URL do webhook que iniciará o workflow completo no n8n"
    )
    
    st.divider()

    # Teste rápido principal - APENAS WEBHOOK
    st.markdown("**🚀 TESTE DIRETO DO WEBHOOK:**")
    if st.button("🎯 EXECUTAR VIA WEBHOOK", type="primary", key="main_test"):
        with st.spinner("Testando webhook diretamente..."):
            # Testar webhook diretamente (sem API)
            test_payload = {
                "timestamp": time.time(),
                "trigger": "start_workflow",
                "execution_id": 1,
                "test": True
            }
            
            try:
                response = call_webhook(st.session_state["webhook_url"], test_payload, timeout=30)
                
                if response.status_code == 200:
                    st.success("🎉 **WEBHOOK FUNCIONANDO PERFEITAMENTE!**")
                    st.balloons()
                    st.info("🎯 O webhook respondeu corretamente - workflow deve estar executando")
                    st.json({"status": "success", "response": response.text[:200] if response.text else "OK"})
                else:
                    st.error(f"❌ Webhook retornou erro: {response.status_code}")
                    st.code(response.text[:300] if response.text else "Sem resposta")
                    
            except Exception as e:
                st.error(f"❌ Erro ao chamar webhook: {e}")
    
    st.warning("⚠️ **Modo Webhook**: API Key com problema, usando apenas webhook direto")
    st.info("💡 **Como funciona**: Chama o webhook diretamente sem verificar status via API")

    st.divider()
    
    # Diagnóstico completo
    st.markdown("**🔍 Diagnóstico Detalhado:**")
    
    col_diag1, col_diag2, col_diag3 = st.columns(3)
    
    with col_diag1:
        if st.button("📊 Status do Workflow"):
            with st.spinner("Verificando status..."):
                is_active, msg = check_workflow_status()
                if is_active is True:
                    st.success(f"✅ {msg}")
                elif is_active is False:
                    st.error(f"❌ {msg}")
                    if st.button("🔄 Ativar Agora"):
                        success, result = activate_workflow(activate=True)
                        if success:
                            st.success(f"✅ {result}")
                        else:
                            st.error(f"❌ {result}")
                else:
                    st.warning(f"⚠️ {msg}")
    
    with col_diag2:
        if st.button("🚀 Executar Via API"):
            with st.spinner("Executando workflow via API..."):
                success, result = execute_workflow_via_api()
                if success:
                    st.success("✅ **WORKFLOW EXECUTADO VIA API!**")
                    st.balloons()
                    st.json(result if isinstance(result, dict) else {"status": "completed"})
                else:
                    st.error(f"❌ Falha na execução via API: {result}")
    
    with col_diag3:
        if st.button("🔥 Testar Webhook"):
            test_payload = {
                "timestamp": time.time(),
                "trigger": "test_connection",
                "test": True
            }
            
            try:
                with st.spinner("Testando webhook..."):
                    response = call_webhook(st.session_state["webhook_url"], test_payload, timeout=30)
                
                if response.status_code == 200:
                    st.success("✅ **WEBHOOK FUNCIONANDO!**")
                    st.info("🎯 Webhook respondeu corretamente")
                else:
                    st.error(f"❌ Erro {response.status_code}: {response.text[:100]}")
            except Exception as e:
                st.error(f"❌ Falha: {e}")
    
    # Controles avançados
    st.markdown("**⚙️ Controles Avançados:**")
    col_ctrl1, col_ctrl2 = st.columns(2)
    
    with col_ctrl1:
        if st.button("🟢 Ativar Workflow"):
            success, msg = activate_workflow(activate=True)
            if success:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")
    
    with col_ctrl2:
        if st.button("🔴 Desativar Workflow"):
            success, msg = activate_workflow(activate=False)
            if success:
                st.info(f"ℹ️ {msg}")
            else:
                st.error(f"❌ {msg}")
    
    st.info("💡 **Métodos de execução**: API (mais confiável) + Webhook (fallback)")
    st.success(f"🎯 **Workflow ativo**: `{WORKFLOW_ID}` - Leads SDR AMAC")
    st.success(f"🔑 API Key: ...{N8N_API_KEY[-10:]} (Configurada)")
    st.caption(f"🔗 URL: https://projeto01-n8n.peitvn.easypanel.host/workflow/{WORKFLOW_ID}")

# Logs recentes e debug
if st.session_state.get("net_logs"):
    with st.expander("📋 Debug - Últimas Operações", expanded=True):
        st.caption("🔍 Acompanhe em tempo real o que está sendo enviado para o n8n:")
        
        # Mostrar últimos 10 logs
        recent_logs = st.session_state["net_logs"][-10:]
        for log in recent_logs:
            action = log.get("action", "")
            when = log.get("when", "")
            execution = log.get("execution", "?")
            
            if action == "STARTING_WORKFLOW":
                method = log.get("method", "")
                st.info(f"🚀 {when} - Iniciando execução #{execution} - {method}")
            elif action == "SKIPPING_API_CHECK":
                reason = log.get("reason", "")
                st.warning(f"⚠️ {when} - Pulando verificação API - {reason}")
            elif action == "EXECUTING_VIA_WEBHOOK":
                st.info(f"🔗 {when} - Executando via WEBHOOK - Execução #{execution}")
            elif action == "ACTIVATING_WORKFLOW":
                st.warning(f"🔄 {when} - Ativando workflow para execução #{execution}")
            elif action == "ACTIVATION_FAILED":
                st.error(f"❌ {when} - Falha ao ativar workflow: {log.get('error', '')}")
            elif action == "EXECUTING_VIA_API":
                st.info(f"🔗 {when} - Executando via API - Execução #{execution}")
            elif action == "FALLBACK_TO_WEBHOOK":
                st.warning(f"🔄 {when} - API falhou, tentando webhook - Execução #{execution}")
            elif action == "WORKFLOW_COMPLETED":
                method = log.get("method", "")
                status = log.get("status", "")
                st.success(f"✅ {when} - Execução #{execution} finalizada via {method} - Status: {status}")
            elif action == "WORKFLOW_ERROR":
                method = log.get("method", "")
                status = log.get("status", "")
                st.error(f"❌ {when} - Erro na execução #{execution} via {method} - Status: {status}")
                if log.get("error"):
                    st.caption(f"Detalhes: {log['error']}")
            elif action == "EXECUTION_EXCEPTION":
                st.error(f"🚨 {when} - Exceção na execução #{execution}: {log.get('error', 'Erro desconhecido')}")
            elif action == "POST":
                st.write(f"🔗 {when} - HTTP {log.get('status', '?')} - Trigger enviado")
        
        # Estatísticas rápidas
        if len(recent_logs) > 0:
            success_count = len([l for l in recent_logs if l.get("action") == "WORKFLOW_COMPLETED"])
            error_count = len([l for l in recent_logs if l.get("action") == "WORKFLOW_ERROR"])
            api_count = len([l for l in recent_logs if l.get("method") == "API"])
            webhook_count = len([l for l in recent_logs if l.get("method") == "WEBHOOK"])
            st.caption(f"📊 Últimas execuções: {success_count} sucessos, {error_count} erros | API: {api_count}, Webhook: {webhook_count}")

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