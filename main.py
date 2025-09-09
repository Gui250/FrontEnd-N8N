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
            "timestamp": time.time(),
            "source": "streamlit_test"
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
        else:
            st.error(f"❌ Webhook retornou erro: {response.status_code}")
            st.code(response.text[:300] if response.text else "Sem resposta")
            return False
            
    except Exception as e:
        st.error(f"❌ Erro ao testar webhook: {e}")
        return False

def execute_webhook1():
    """Executa o Webhook1 com dados de teste para o Google Sheets."""
    try:
        # Dados de teste para o workflow processar
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
                "disparo": "nao"  # Para que passe pelo filtro If1
            },
            {
                "nome_empresa": "Academia Fitness Pro",
                "telefone": "11888888888",
                "endereco": "Rio de Janeiro, RJ, Brasil",
                "website": "https://academia-pro.com.br",
                "rating": "4.8",
                "reviews": "200",
                "especialidades": "Academia, Fitness, Musculação",
                "mensagem": "",
                "disparo": "nao"
            }
        ]
        
        st.session_state["operation_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "action": "🚀 INICIANDO_WEBHOOK1",
            "details": f"Enviando {len(test_data)} empresas para processamento"
        })
        
        # Payload no formato esperado pelo workflow
        payload = {
            "empresas": test_data,
            "timestamp": time.time(),
            "source": "streamlit_controller"
        }
        
        # Chamar Webhook1
        response = call_webhook(WEBHOOK_LEADS, payload, timeout=60)
        
        if response.status_code == 200:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "✅ WEBHOOK1_SUCCESS",
                "details": f"Workflow executado com sucesso! Status: {response.status_code}"
            })
            return True, "Webhook1 executado com sucesso! O workflow está processando os dados."
        else:
            st.session_state["operation_logs"].append({
                "timestamp": time.strftime("%H:%M:%S"),
                "action": "❌ WEBHOOK1_ERROR",
                "details": f"Erro {response.status_code}: {response.text[:100]}"
            })
            return False, f"Erro {response.status_code}: {response.text[:200]}"
            
    except Exception as e:
        st.session_state["operation_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "action": "🚨 WEBHOOK1_EXCEPTION",
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
st.set_page_config(layout="wide", page_title="Webhook1 Controller", page_icon="🚀")
st.title("🚀 Controle do Webhook1 - AMAC Leads")

# Informações do workflow
st.info(f"🎯 **Workflow ID**: `{WORKFLOW_ID}` | 🔗 [Abrir no n8n]({N8N_BASE_URL}/workflow/{WORKFLOW_ID})")

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
st.markdown("## 🎯 Controle do Webhook1")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🚀 Executar Webhook1")
    st.info("""
    **Fluxo**: Webhook1 → Code → Google Sheets → If1 → Filter → Loop → Scraping → AI → Mensagens
    
    **Função**: Processa leads, faz scraping dos sites, gera mensagens com AI e envia via WhatsApp
    """)
    
    if st.button("🚀 EXECUTAR WEBHOOK1", type="primary", use_container_width=True):
        with st.spinner("Executando Webhook1..."):
            success, message = execute_webhook1()
            if success:
                st.success(f"✅ {message}")
                st.balloons()
            else:
                st.error(f"❌ {message}")

with col2:
    st.markdown("### 🔍 Testar Conectividade")
    st.info("""
    **Teste**: Verifica se o Webhook1 está respondendo corretamente
    
    **Resultado**: Status 200 = OK, outros = problema
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
    - Use o botão "🚀 EXECUTAR WEBHOOK1" nesta página
    - O workflow processará os dados automaticamente
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
    
    **📋 Estrutura do Payload**:
    ```json
    {{
      "empresas": [
        {{
          "nome_empresa": "Nome da Empresa",
          "telefone": "11999999999",
          "website": "https://site.com.br",
          "rating": "4.5",
          "reviews": "100",
          "especialidades": "Área de atuação",
          "mensagem": "",
          "disparo": "nao"
        }}
      ],
      "timestamp": 1234567890,
      "source": "streamlit_controller"
    }}
    ```
    
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
st.caption("🚀 Webhook1 Controller - Versão simplificada sem dependência de API")