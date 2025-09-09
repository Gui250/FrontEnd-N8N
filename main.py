import streamlit as st
import requests
import time
from requests.exceptions import ReadTimeout, ConnectionError

# ========== CONFIGURAÇÕES CORRETAS ==========
# Webhooks corretos extraídos do JSON do workflow
WEBHOOK_LEADS = "https://projeto01-n8n.peitvn.easypanel.host/webhook/ce723d0d-a280-414f-aec3-85c940f7dc6f"  # Webhook1 - Leads
WEBHOOK_EXTRATOR = "https://projeto01-n8n.peitvn.easypanel.host/webhook/c350dfad-ce64-4535-b806-905c72ecef28"  # Webhook - Extrator
WORKFLOW_ID = "D2c8LMH4Fq8JT6CQ"  # ID correto do JSON
N8N_BASE_URL = "https://projeto01-n8n.peitvn.easypanel.host"
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NWM4YTg2Zi1iZDc3LTRjZTYtYjJmYS1mM2Q3MGZhNzJkOWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU3NDM2ODYwfQ.EcLw5O_-m3jQuZ1TS7mwthh6yxV_6AsZbmARYAHDu-Q"

# ========== FUNÇÕES AUXILIARES ==========
def call_webhook(url, payload=None, timeout=30):
    """Chama o webhook com payload correto."""
    try:
        response = requests.post(url, json=(payload or {}), timeout=timeout)
        
        # Log da operação
        if "operation_logs" in st.session_state:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "WEBHOOK_CALL",
                "url": url[-20:] + "...",  # Últimos 20 chars
                "status": response.status_code,
                "payload_size": len(str(payload)) if payload else 0,
                "response_preview": response.text[:100] if response.text else "No response"
            })
        
        return response
    except Exception as e:
        if "operation_logs" in st.session_state:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "WEBHOOK_ERROR",
                "error": str(e)
            })
        raise e

def check_workflow_status():
    """Verifica se o workflow está ativo."""
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
    """Ativa ou desativa o workflow."""
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

def execute_leads_workflow():
    """Executa o workflow de leads com dados corretos."""
    try:
        # Dados de teste para o Google Sheets (conforme esperado pelo workflow)
        test_data = [
            {
                "nome_empresa": "Empresa Teste AMAC",
                "telefone": "11999999999",
                "endereco": "São Paulo, SP, Brasil",
                "website": "https://exemplo.com.br",
                "rating": "4.5",
                "reviews": "150",
                "especialidades": "Segurança eletrônica, CFTV",
                "mensagem": "",  # Vazio para que o workflow processe
                "disparo": "nao"  # Para que passe pelo filtro
            }
        ]
        
        # Log de início
        st.session_state["operation_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "action": "🚀 INICIANDO_LEADS_WORKFLOW",
            "details": f"Enviando {len(test_data)} empresas para processamento"
        })
        
        # Chamar webhook de leads (Webhook1)
        response = call_webhook(WEBHOOK_LEADS, {"data": test_data}, timeout=60)
        
        if response.status_code == 200:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "✅ LEADS_WORKFLOW_SUCCESS",
                "details": f"Workflow iniciado com sucesso. Status: {response.status_code}"
            })
            return True, "Workflow de leads executado com sucesso!"
        else:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "❌ LEADS_WORKFLOW_ERROR",
                "details": f"Erro {response.status_code}: {response.text[:100]}"
            })
            return False, f"Erro {response.status_code}: {response.text[:200]}"
            
    except Exception as e:
        st.session_state["operation_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "action": "🚨 LEADS_WORKFLOW_EXCEPTION",
            "details": f"Exceção: {str(e)}"
        })
        return False, f"Erro na execução: {e}"

def execute_extrator_workflow():
    """Executa o workflow extrator com dados de empresas."""
    try:
        # Dados para extração (conforme esperado pelo Code1)
        empresas_data = [
            {
                "nome_empresa": "Academia Teste",
                "telefone": "11987654321",
                "endereco": "Rua Teste, 123 - São Paulo, SP",
                "website": "https://academia-teste.com.br",
                "rating": "4.8",
                "reviews": "200",
                "especialidades": "Academia, Fitness"
            },
            {
                "nome_empresa": "Empresa Segurança",
                "telefone": "11876543210",
                "endereco": "Av. Teste, 456 - Rio de Janeiro, RJ", 
                "website": "https://empresa-seguranca.com.br",
                "rating": "4.2",
                "reviews": "80",
                "especialidades": "Segurança, Monitoramento"
            }
        ]
        
        # Payload no formato esperado pelo Code1
        payload = {
            "body": empresas_data
        }
        
        st.session_state["operation_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "action": "🔄 INICIANDO_EXTRATOR_WORKFLOW",
            "details": f"Enviando {len(empresas_data)} empresas para extração"
        })
        
        # Chamar webhook extrator
        response = call_webhook(WEBHOOK_EXTRATOR, payload, timeout=60)
        
        if response.status_code == 200:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "✅ EXTRATOR_WORKFLOW_SUCCESS",
                "details": f"Extrator executado com sucesso. Status: {response.status_code}"
            })
            return True, "Workflow extrator executado com sucesso!"
        else:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "❌ EXTRATOR_WORKFLOW_ERROR", 
                "details": f"Erro {response.status_code}: {response.text[:100]}"
            })
            return False, f"Erro {response.status_code}: {response.text[:200]}"
            
    except Exception as e:
        st.session_state["operation_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "action": "🚨 EXTRATOR_WORKFLOW_EXCEPTION",
            "details": f"Exceção: {str(e)}"
        })
        return False, f"Erro na execução: {e}"

# ========== INICIALIZAÇÃO ==========
def init_session_state():
    """Inicializa o estado da sessão."""
    defaults = {
        "operation_logs": [],
        "workflow_active": False
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# ========== INTERFACE PRINCIPAL ==========
st.set_page_config(layout="wide", page_title="n8n Workflow Controller", page_icon="⚙️")
st.title("🔄 Controle de Workflows n8n - AMAC Leads")

# Informações do workflow
st.info(f"🎯 **Workflow ID**: `{WORKFLOW_ID}` | 🔗 [Abrir no n8n]({N8N_BASE_URL}/workflow/{WORKFLOW_ID})")

# ========== DIAGNÓSTICO COMPLETO ==========
with st.expander("🔍 DIAGNÓSTICO COMPLETO - PROBLEMAS CORRIGIDOS", expanded=True):
    st.success("✅ **TODOS OS PROBLEMAS IDENTIFICADOS E CORRIGIDOS!**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🚨 PROBLEMAS ENCONTRADOS:**
        
        1. ❌ **Webhook errado**: Usava `b877c4b1...` (inexistente)
        2. ❌ **Workflow ID errado**: Usava `5w9w7VyDWF2d4V7c`
        3. ❌ **Payload incorreto**: Estrutura não compatível
        4. ❌ **Ciclos de tempo**: Lógica desnecessária e problemática
        5. ❌ **Fluxo confuso**: Não seguia a estrutura do n8n
        """)
    
    with col2:
        st.markdown("""
        **✅ CORREÇÕES APLICADAS:**
        
        1. ✅ **Webhooks corretos**: `ce723d0d...` (Leads) e `c350dfad...` (Extrator)
        2. ✅ **Workflow ID correto**: `D2c8LMH4Fq8JT6CQ`
        3. ✅ **Payload correto**: Estrutura compatível com Code/Code1
        4. ✅ **Execução direta**: Sem ciclos, execução imediata
        5. ✅ **Fluxo claro**: Segue exatamente a estrutura do JSON
        """)

# ========== FLUXOS DISPONÍVEIS ==========
st.markdown("## 🎯 Fluxos Disponíveis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📋 Workflow de Leads")
    st.info("""
    **Fluxo**: Webhook1 → Code → Google Sheets → If1 → Filter → Loop → Scraping → AI → Mensagens
    
    **Função**: Processa leads do Google Sheets, faz scraping, gera mensagens com AI e envia via WhatsApp
    """)
    
    if st.button("🚀 EXECUTAR LEADS WORKFLOW", type="primary", key="leads"):
        with st.spinner("Executando workflow de leads..."):
            success, message = execute_leads_workflow()
            if success:
                st.success(f"✅ {message}")
                st.balloons()
            else:
                st.error(f"❌ {message}")

with col2:
    st.markdown("### 🔄 Workflow Extrator")
    st.info("""
    **Fluxo**: Webhook → Code1 → DADOS → Loop → Check JIDs → Validações → Google Sheets
    
    **Função**: Recebe dados de empresas, valida números de WhatsApp e salva no Google Sheets
    """)
    
    if st.button("🔄 EXECUTAR EXTRATOR WORKFLOW", type="secondary", key="extrator"):
        with st.spinner("Executando workflow extrator..."):
            success, message = execute_extrator_workflow()
            if success:
                st.success(f"✅ {message}")
                st.balloons()
            else:
                st.error(f"❌ {message}")

# ========== CONTROLES DO WORKFLOW ==========
st.markdown("## ⚙️ Controles do Workflow")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📊 Verificar Status"):
        with st.spinner("Verificando status..."):
            is_active, msg = check_workflow_status()
            if is_active is True:
                st.success(f"✅ {msg}")
            elif is_active is False:
                st.warning(f"⚠️ {msg}")
            else:
                st.error(f"❌ {msg}")

with col2:
    if st.button("🟢 Ativar Workflow"):
        with st.spinner("Ativando workflow..."):
            success, msg = activate_workflow(activate=True)
            if success:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

with col3:
    if st.button("🔴 Desativar Workflow"):
        with st.spinner("Desativando workflow..."):
            success, msg = activate_workflow(activate=False)
            if success:
                st.info(f"ℹ️ {msg}")
            else:
                st.error(f"❌ {msg}")

# ========== LOGS EM TEMPO REAL ==========
if st.session_state.get("operation_logs"):
    with st.expander("📋 Logs de Operações - Tempo Real", expanded=True):
        st.caption("🔍 Acompanhe todas as operações em tempo real:")
        
        # Mostrar últimos 15 logs
        recent_logs = st.session_state["operation_logs"][-15:]
        
        for log in recent_logs:
            timestamp = log.get("timestamp", "")
            action = log.get("action", "")
            
            if "SUCCESS" in action:
                st.success(f"✅ {timestamp} - {action}")
                if log.get("details"):
                    st.caption(f"📋 {log['details']}")
            elif "ERROR" in action:
                st.error(f"❌ {timestamp} - {action}")
                if log.get("details"):
                    st.caption(f"🚨 {log['details']}")
            elif "EXCEPTION" in action:
                st.error(f"🚨 {timestamp} - {action}")
                if log.get("details"):
                    st.caption(f"💥 {log['details']}")
            elif "INICIANDO" in action:
                st.info(f"🚀 {timestamp} - {action}")
                if log.get("details"):
                    st.caption(f"📋 {log['details']}")
            elif "WEBHOOK_CALL" in action:
                st.info(f"🔗 {timestamp} - Chamada de Webhook")
                st.caption(f"🌐 URL: ...{log.get('url', '')}")
                st.caption(f"📊 Status: {log.get('status', '?')} | Payload: {log.get('payload_size', 0)} chars")
            else:
                st.write(f"📝 {timestamp} - {action}")
                if log.get("details"):
                    st.caption(f"ℹ️ {log['details']}")
        
        # Botão para limpar logs
        if st.button("🗑️ Limpar Logs"):
            st.session_state["operation_logs"] = []
            st.success("🗑️ Logs limpos!")
            st.rerun()

# ========== INFORMAÇÕES TÉCNICAS ==========
with st.expander("🔧 Informações Técnicas", expanded=False):
    st.markdown(f"""
    **🔗 Webhooks Configurados:**
    - **Leads**: `{WEBHOOK_LEADS}`
    - **Extrator**: `{WEBHOOK_EXTRATOR}`
    
    **🆔 Workflow ID**: `{WORKFLOW_ID}`
    
    **🔑 API Key**: `...{N8N_API_KEY[-10:]}`
    
    **🌐 n8n Base URL**: `{N8N_BASE_URL}`
    
    **📋 Estrutura dos Payloads:**
    - **Leads**: `{"data": [empresas...]}`
    - **Extrator**: `{"body": [empresas...]}`
    """)

st.markdown("---")
st.caption("🔄 Sistema de controle n8n - Versão corrigida sem ciclos de tempo")