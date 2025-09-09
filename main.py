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
    """Testa a conectividade do webhook com diagnóstico avançado."""
    try:
        st.info("🔍 Testando conectividade do Webhook1...")
        
        # Teste 1: Verificar URL
        st.write("**1. Verificando URL do webhook...**")
        st.code(WEBHOOK_LEADS)
        
        # Teste 2: Payload mínimo
        test_payload = {
            "test": True,
            "timestamp": time.time()
        }
        
        st.write("**2. Enviando payload de teste...**")
        st.json(test_payload)
        
        response = call_webhook(WEBHOOK_LEADS, test_payload, timeout=15)
        
        # Teste 3: Análise da resposta
        st.write("**3. Análise da resposta:**")
        st.write(f"**Status Code:** {response.status_code}")
        st.write(f"**Headers:** {dict(response.headers)}")
        st.write(f"**Response Text:** {response.text[:500]}...")
        
        st.session_state["operation_logs"].append({
            "timestamp": time.strftime("%H:%M:%S"),
            "action": "CONNECTION_TEST",
            "status": response.status_code,
            "details": f"Teste de conectividade - Status: {response.status_code}",
            "response_text": response.text[:200],
            "headers": dict(response.headers)
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
            st.code(response.text[:500] if response.text else "Sem resposta")
            return False
            
    except Exception as e:
        st.error(f"❌ Erro ao testar webhook: {e}")
        st.exception(e)
        return False

def diagnose_workflow_issue():
    """Diagnóstico completo do workflow."""
    st.markdown("### 🔧 DIAGNÓSTICO COMPLETO")
    
    # Teste 1: Verificar se o n8n está online
    st.write("**1. Testando se o n8n está online...**")
    try:
        base_response = requests.get(N8N_BASE_URL, timeout=10)
        if base_response.status_code == 200:
            st.success("✅ n8n está online e respondendo")
        else:
            st.error(f"❌ n8n retornou status {base_response.status_code}")
    except Exception as e:
        st.error(f"❌ n8n não está acessível: {e}")
    
    # Teste 2: Verificar estrutura da URL do webhook
    st.write("**2. Verificando estrutura da URL...**")
    webhook_parts = WEBHOOK_LEADS.split('/')
    st.write(f"- **Base URL**: {'/'.join(webhook_parts[:-2])}")
    st.write(f"- **Endpoint**: /{'/'.join(webhook_parts[-2:])}")
    st.write(f"- **Webhook ID**: {webhook_parts[-1]}")
    
    # Teste 3: Tentar diferentes payloads
    st.write("**3. Testando diferentes estruturas de payload...**")
    
    payloads_to_test = [
        {"test": True},
        {},
        {"trigger": "start"},
        {"data": "test"},
        None
    ]
    
    for i, payload in enumerate(payloads_to_test, 1):
        try:
            st.write(f"**Teste {i}**: {payload}")
            response = requests.post(WEBHOOK_LEADS, json=payload, timeout=10)
            st.write(f"Status: {response.status_code} | Response: {response.text[:100]}")
        except Exception as e:
            st.write(f"Erro: {e}")
    
    # Teste 4: Verificar método HTTP
    st.write("**4. Testando diferentes métodos HTTP...**")
    for method in ['POST', 'GET']:
        try:
            if method == 'POST':
                response = requests.post(WEBHOOK_LEADS, json={"test": True}, timeout=10)
            else:
                response = requests.get(WEBHOOK_LEADS, timeout=10)
            st.write(f"**{method}**: Status {response.status_code}")
        except Exception as e:
            st.write(f"**{method}**: Erro - {e}")

def test_alternative_webhook_urls():
    """Testa URLs alternativas do webhook."""
    st.markdown("### 🔄 TESTANDO URLs ALTERNATIVAS")
    
    # URLs alternativas baseadas no JSON
    alternative_urls = [
        f"{N8N_BASE_URL}/webhook-test/ce723d0d-a280-414f-aec3-85c940f7dc6f",
        f"{N8N_BASE_URL}/webhook/test/ce723d0d-a280-414f-aec3-85c940f7dc6f",
        f"{N8N_BASE_URL}/api/webhook/ce723d0d-a280-414f-aec3-85c940f7dc6f",
        f"{N8N_BASE_URL}/production/webhook/ce723d0d-a280-414f-aec3-85c940f7dc6f"
    ]
    
    for i, url in enumerate(alternative_urls, 1):
        st.write(f"**Teste {i}**: {url}")
        try:
            response = requests.post(url, json={"test": True}, timeout=5)
            if response.status_code == 200:
                st.success(f"✅ URL alternativa funcionou! Status: {response.status_code}")
                st.write(f"**Nova URL funcional**: {url}")
                return url
            else:
                st.write(f"Status: {response.status_code}")
        except Exception as e:
            st.write(f"Erro: {e}")
    
    st.warning("❌ Nenhuma URL alternativa funcionou")
    return None

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

# ========== DIAGNÓSTICO AVANÇADO ==========
st.markdown("## 🔧 Diagnóstico Avançado")

col_diag1, col_diag2, col_diag3 = st.columns(3)

with col_diag1:
    if st.button("🔧 DIAGNÓSTICO COMPLETO", use_container_width=True):
        diagnose_workflow_issue()

with col_diag2:
    if st.button("🔄 TESTAR URLs ALTERNATIVAS", use_container_width=True):
        alternative_url = test_alternative_webhook_urls()
        if alternative_url:
            st.info(f"💡 Considere usar: {alternative_url}")

with col_diag3:
    if st.button("📋 VERIFICAR JSON WORKFLOW", use_container_width=True):
        st.markdown("### 📋 Informações do Workflow JSON")
        st.write("**Webhook ID encontrado no JSON**: ce723d0d-a280-414f-aec3-85c940f7dc6f")
        st.write("**Nome do node**: Webhook1")
        st.write("**Método HTTP**: POST")
        st.write("**Response Mode**: responseNode")
        st.write("**Conexão**: Webhook1 → Code → Get row(s) in sheet")

# ========== SOLUÇÕES RÁPIDAS ==========
with st.expander("🚨 SOLUÇÕES RÁPIDAS - SE O FLUXO NÃO FUNCIONA", expanded=True):
    st.error("🚨 **PROBLEMA**: O fluxo não inicia no n8n")
    
    col_sol1, col_sol2 = st.columns(2)
    
    with col_sol1:
        st.markdown("""
        **🔧 CHECKLIST RÁPIDO:**
        
        1. ✅ **Workflow ativo?**
           - Acesse o n8n
           - Toggle "Active" deve estar verde
        
        2. ✅ **URL correta?**
           - Use o diagnóstico acima
           - Teste URLs alternativas
        
        3. ✅ **n8n online?**
           - Acesse: https://projeto01-n8n.peitvn.easypanel.host
           - Deve carregar a interface
        """)
    
    with col_sol2:
        st.markdown("""
        **🎯 SOLUÇÕES MAIS COMUNS:**
        
        1. **Reativar o workflow**:
           - Desative e ative novamente
           - Aguarde 30 segundos
        
        2. **Usar URL de teste**:
           - No n8n, use a URL de teste
           - Depois mude para produção
        
        3. **Verificar Google Sheets**:
           - Deve ter dados para processar
           - Coluna "mensagem" deve estar vazia
        """)
    
    st.warning("💡 **DICA**: Use o 'DIAGNÓSTICO COMPLETO' acima para identificar o problema exato")

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
st.caption("🚀 Webhook1 Controller - Versão simplificada sem dependência de API")