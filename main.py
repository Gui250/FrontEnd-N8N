import streamlit as st
import requests
import time
from requests.exceptions import ReadTimeout, ConnectionError

# ========== CONFIGURAÇÕES CORRETAS ==========
# Webhook1 - Único webhook que vamos usar (Leads)
WEBHOOK_LEADS = "https://projeto01-n8n.peitvn.easypanel.host/webhook/ce723d0d-a280-414f-aec3-85c940f7dc6f"
WORKFLOW_ID = "D2c8LMH4Fq8JT6CQ"
N8N_BASE_URL = "https://projeto01-n8n.peitvn.easypanel.host"

# ========== FUNÇÕES AUXILIARES ==========
def call_webhook(url, payload=None, timeout=30):
    """Chama o webhook com payload."""
    try:
        response = requests.post(url, json=(payload or {}), timeout=timeout)
        
        # Log da operação
        if "operation_logs" in st.session_state:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "WEBHOOK_CALL",
                "status": response.status_code,
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

def test_webhook_connection():
    """Testa a conectividade do webhook."""
    try:
        st.info("🔍 Testando conectividade do Webhook1...")
        
        test_payload = {
            "test": True,
            "timestamp": time.time()
        }
        
        response = call_webhook(WEBHOOK_LEADS, test_payload, timeout=15)
        
        st.session_state["operation_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "action": "CONNECTION_TEST",
            "status": response.status_code,
            "details": f"Teste de conectividade - Status: {response.status_code}"
        })
        
        if response.status_code == 200:
            st.success("✅ Webhook1 está funcionando perfeitamente!")
            st.balloons()
            return True
        elif response.status_code == 404:
            st.error("🚨 **WEBHOOK NÃO REGISTRADO (404)**")
            st.error("❌ O workflow não está ativo no n8n!")
            show_activation_instructions()
            return False
        else:
            st.error(f"❌ Webhook retornou erro: {response.status_code}")
            st.code(response.text[:300] if response.text else "Sem resposta")
            return False
            
    except Exception as e:
        st.error(f"❌ Erro ao testar webhook: {e}")
        return False

def show_activation_instructions():
    """Mostra instruções detalhadas para ativar o workflow."""
    st.markdown("### 🔧 INSTRUÇÕES PARA ATIVAR O WORKFLOW:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📋 PASSO A PASSO:**
        1. **Acesse**: https://projeto01-n8n.peitvn.easypanel.host
        2. **Faça login** na sua conta n8n
        3. **Encontre o workflow**: "Leads sdr AMAC - FUNCIONANDO copy"
        4. **Abra o workflow** clicando nele
        5. **Ative**: Clique no toggle "Active" (canto superior direito)
        6. **Confirme**: O toggle deve ficar verde
        """)
    
    with col2:
        st.markdown("""
        **✅ COMO SABER SE ESTÁ ATIVO:**
        - Toggle "Active" deve estar **verde/ligado**
        - Aparece "Active" ao lado do nome do workflow
        - Webhook fica disponível para receber requisições
        
        **🔄 DEPOIS DE ATIVAR:**
        - Volte aqui e clique "🚀 INICIAR FLUXO"
        - Deve iniciar o processamento dos leads
        """)
    
    st.warning("⚠️ **IMPORTANTE**: O workflow DEVE estar ativo para o webhook funcionar!")
    
    if st.button("🔄 TESTAR NOVAMENTE APÓS ATIVAÇÃO", key="retest"):
        st.rerun()

def iniciar_fluxo():
    """Inicia o fluxo do workflow sem enviar dados específicos."""
    try:
        st.session_state["operation_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "action": "🚀 INICIANDO_FLUXO",
            "details": "Disparando o workflow para processar dados do Google Sheets"
        })
        
        # Payload mínimo apenas para iniciar o fluxo
        payload = {
            "trigger": "start_workflow",
            "timestamp": time.time(),
            "source": "streamlit_trigger"
        }
        
        # Chamar Webhook1 apenas para iniciar
        response = call_webhook(WEBHOOK_LEADS, payload, timeout=60)
        
        if response.status_code == 200:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "✅ FLUXO_INICIADO",
                "details": f"Fluxo iniciado com sucesso! Status: {response.status_code}"
            })
            return True, "🚀 Fluxo iniciado! O workflow está processando os dados do Google Sheets."
        elif response.status_code == 404:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "❌ WORKFLOW_INATIVO",
                "details": "Workflow não está ativo - erro 404"
            })
            return False, "WORKFLOW NÃO ESTÁ ATIVO! Você precisa ativar o workflow no n8n primeiro."
        else:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "❌ ERRO_FLUXO",
                "details": f"Erro {response.status_code}: {response.text[:100]}"
            })
            return False, f"Erro {response.status_code}: {response.text[:200]}"
            
    except Exception as e:
        st.session_state["operation_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "action": "🚨 EXCECAO_FLUXO",
            "details": f"Exceção: {str(e)}"
        })
        return False, f"Erro na execução: {e}"

# ========== INICIALIZAÇÃO ==========
def init_session_state():
    """Inicializa o estado da sessão."""
    if "operation_logs" not in st.session_state:
        st.session_state["operation_logs"] = []

init_session_state()

# ========== INTERFACE PRINCIPAL ==========
st.set_page_config(layout="wide", page_title="Iniciar Fluxo AMAC", page_icon="🚀")
st.title("🚀 Iniciar Fluxo de Leads - AMAC")

# Informações do workflow
st.info(f"🎯 **Workflow ID**: `{WORKFLOW_ID}` | 🔗 [Abrir no n8n]({N8N_BASE_URL}/workflow/{WORKFLOW_ID})")

# Verificação automática do status do workflow
def check_workflow_status_display():
    """Verifica e exibe o status do workflow."""
    try:
        test_payload = {"status_check": True}
        response = requests.post(WEBHOOK_LEADS, json=test_payload, timeout=5)
        
        if response.status_code == 200:
            st.success("✅ **WORKFLOW ATIVO** - Pronto para processar leads!")
            return True
        elif response.status_code == 404:
            st.error("🚨 **WORKFLOW INATIVO** - Você precisa ativar o workflow no n8n!")
            st.error("👆 **CLIQUE NO LINK ACIMA** para abrir o n8n e ativar o workflow")
            return False
        else:
            st.warning(f"⚠️ **STATUS INCERTO** - Webhook retornou {response.status_code}")
            return False
    except:
        st.warning("⚠️ **NÃO FOI POSSÍVEL VERIFICAR** - Teste manualmente abaixo")
        return False

# Verificar status automaticamente
workflow_active = check_workflow_status_display()

# ========== PROBLEMA DA API RESOLVIDO ==========
with st.expander("🔧 PROBLEMA DE AUTORIZAÇÃO RESOLVIDO", expanded=True):
    st.success("✅ **SOLUÇÃO**: Removemos a dependência da API com erro 401")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🚨 PROBLEMA IDENTIFICADO:**
        - ❌ API Key com erro 401 Unauthorized
        - ❌ Não conseguia ativar/desativar workflow
        - ❌ Funcionalidades bloqueadas pela API
        """)
    
    with col2:
        st.markdown("""
        **✅ SOLUÇÃO IMPLEMENTADA:**
        - ✅ **Webhook direto** sem dependência da API
        - ✅ **Execução imediata** do Webhook1
        - ✅ **Foco apenas no essencial** - processar leads
        """)

# ========== CONTROLE PRINCIPAL ==========
st.markdown("## 🎯 Controle do Fluxo de Leads")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🚀 Iniciar Fluxo")
    st.info("""
    **Fluxo**: Webhook1 → Code → Google Sheets → If1 → Filter → Loop → Scraping → AI → Mensagens
    
    **Função**: Inicia o processamento dos leads que estão no Google Sheets
    """)
    
    if st.button("🚀 INICIAR FLUXO", type="primary", use_container_width=True):
        with st.spinner("Iniciando fluxo..."):
            success, message = iniciar_fluxo()
            if success:
                st.success(f"✅ {message}")
                st.balloons()
            else:
                st.error(f"❌ {message}")
                if "NÃO ESTÁ ATIVO" in message:
                    show_activation_instructions()

with col2:
    st.markdown("### 🔍 Testar Conectividade")
    st.info("""
    **Teste**: Verifica se o Webhook1 está respondendo corretamente
    
    **Resultado**: Status 200 = OK, Status 404 = Workflow inativo
    """)
    
    if st.button("🔍 TESTAR WEBHOOK1", type="secondary", use_container_width=True):
        test_webhook_connection()

# ========== INSTRUÇÕES MANUAIS ==========
st.markdown("## ⚙️ Instruções para Ativar Manualmente")

with st.expander("📋 Como ativar o workflow no n8n (Manual)", expanded=False):
    st.markdown("""
    **🔧 PASSO A PASSO para ativar o workflow:**
    
    1. **Acesse o n8n**: https://projeto01-n8n.peitvn.easypanel.host
    2. **Faça login** na sua conta
    3. **Abra o workflow**: Clique em "Leads sdr AMAC - FUNCIONANDO copy"
    4. **Ative o workflow**: Clique no toggle "Active" no canto superior direito
    5. **Confirme**: O toggle deve ficar verde/ativo
    
    **✅ Pronto!** O Webhook1 estará ativo e funcionando.
    
    **🎯 Depois de ativar manualmente:**
    - Use o botão "🚀 INICIAR FLUXO" nesta página
    - O workflow processará os leads do Google Sheets automaticamente
    - Acompanhe os logs abaixo para ver o progresso
    """)

# ========== LOGS EM TEMPO REAL ==========
if st.session_state.get("operation_logs"):
    with st.expander("📋 Logs de Operações - Tempo Real", expanded=True):
        st.caption("🔍 Acompanhe todas as operações do Webhook1:")
        
        # Mostrar últimos 10 logs
        recent_logs = st.session_state["operation_logs"][-10:]
        
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
            elif "CONNECTION_TEST" in action:
                status = log.get("status", "?")
                if status == 200:
                    st.success(f"✅ {timestamp} - Teste de Conectividade")
                else:
                    st.error(f"❌ {timestamp} - Teste de Conectividade")
                if log.get("details"):
                    st.caption(f"🔍 {log['details']}")
            elif "WEBHOOK_CALL" in action:
                status = log.get("status", "?")
                if status == 200:
                    st.success(f"🔗 {timestamp} - Webhook chamado com sucesso")
                else:
                    st.error(f"🔗 {timestamp} - Erro na chamada do webhook")
                st.caption(f"📊 Status: {status}")
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
    **🔗 Webhook1 URL**: 
    `{WEBHOOK_LEADS}`
    
    **🆔 Workflow ID**: `{WORKFLOW_ID}`
    
    **🌐 n8n Base URL**: `{N8N_BASE_URL}`
    
    **📋 Payload de Inicialização**:
    ```json
    {{
      "trigger": "start_workflow",
      "timestamp": 1234567890,
      "source": "streamlit_trigger"
    }}
    ```
    
    **ℹ️ Como funciona**:
    - O webhook apenas **inicia** o fluxo
    - O workflow processa os dados que já estão no **Google Sheets**
    - Não enviamos dados específicos, apenas disparamos o processamento
    
    **🎯 Fluxo do Workflow**:
    1. Webhook1 recebe os dados
    2. Code gera número aleatório
    3. Get row(s) in sheet busca dados no Google Sheets
    4. If1 filtra registros com mensagem não vazia
    5. Filter filtra registros válidos
    6. Loop Over Items processa cada empresa
    7. Jina AI faz scraping do site
    8. Message a model gera mensagem com GPT
    9. Envia MSG Texto via WhatsApp
    """)

st.markdown("---")
st.caption("🚀 Iniciar Fluxo - Versão simplificada que apenas dispara o workflow")