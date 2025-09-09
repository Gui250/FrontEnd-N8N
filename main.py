import streamlit as st
import requests
import time
import json
import base64
import threading
from requests.exceptions import ReadTimeout
try:
    from streamlit_lottie import st_lottie
except Exception:
    st_lottie = None



WEBHOOK_MAIN_URL = "https://projeto01-n8n.peitvn.easypanel.host/webhook/b877c4b1-4eb2-475f-aead-117d6d89614c"
WORKFLOW_ID = "D2c8LMH4Fq8JT6CQ"  # ID extraído do arquivo JSON do workflow



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

if "processed_numbers" not in st.session_state:
    st.session_state["processed_numbers"] = set()

if "message_history" not in st.session_state:
    st.session_state["message_history"] = {}  # {numero: {"timestamp": ..., "status": ..., "message": ...}}

if "leads_data" not in st.session_state:
    st.session_state["leads_data"] = []

# Configuração de detecção de duplicatas removida - fluxo roda até parada manual

if "last_processed_number" not in st.session_state:
    st.session_state["last_processed_number"] = None

if "n8n_api_key" not in st.session_state:
    st.session_state["n8n_api_key"] = ""

if "workflow_id" not in st.session_state:
    st.session_state["workflow_id"] = ""

if "loop_active" not in st.session_state:
    st.session_state["loop_active"] = False

if "loop_count" not in st.session_state:
    st.session_state["loop_count"] = 0

if "loop_thread" not in st.session_state:
    st.session_state["loop_thread"] = None

if "loop_stop_flag" not in st.session_state:
    st.session_state["loop_stop_flag"] = False

if "loop_delay" not in st.session_state:
    st.session_state["loop_delay"] = 10  # Delay padrão de 10 segundos entre chamadas

if "skipped_cycles" not in st.session_state:
    st.session_state["skipped_cycles"] = 0  # Contador de ciclos pulados por duplicatas

st.write(f"📌 Status atual: **{st.session_state['status']}**")

# Mostrar informações do loop se estiver ativo
if st.session_state.get("loop_active", False):
    col_loop1, col_loop2, col_loop3, col_loop4 = st.columns(4)
    with col_loop1:
        st.metric("🔄 Loop Ativo", "SIM", delta="Executando continuamente")
    with col_loop2:
        loop_count = st.session_state.get("loop_count", 0)
        st.metric("📊 Total de Ciclos", loop_count)
    with col_loop3:
        unique_numbers = len(st.session_state.get("message_history", {}))
        st.metric("📱 Números Únicos", unique_numbers, delta="Mensagens enviadas")
    with col_loop4:
        skipped = st.session_state.get("skipped_cycles", 0)
        st.metric("⏭️ Ciclos Pulados", skipped, delta="Duplicatas evitadas")
    
    # Segunda linha de métricas
    col_time1, col_time2, col_time3 = st.columns(3)
    with col_time1:
        if "execution_start_time" in st.session_state:
            runtime = time.time() - st.session_state["execution_start_time"]
            st.metric("⏱️ Tempo Ativo", f"{runtime:.0f}s")
        else:
            st.metric("⏱️ Tempo Ativo", "0s")
    with col_time2:
        if loop_count > 0:
            efficiency = (unique_numbers / loop_count) * 100
            st.metric("📈 Eficiência", f"{efficiency:.1f}%", delta="Novos números/ciclos")
        else:
            st.metric("📈 Eficiência", "0%")
    with col_time3:
        next_call = st.session_state.get("loop_delay", 10)
        st.metric("⏳ Próxima Chamada", f"{next_call}s", delta="Intervalo configurado")
    
    st.success("🟢 **LOOP INTELIGENTE ATIVO** - Enviando apenas uma mensagem por número único")
    st.info("💡 Para parar o loop, clique no botão 'Parar Fluxo' abaixo")
    st.info("🛡️ Duplicatas são automaticamente detectadas e puladas, mantendo o loop ativo")
    
    # Auto-refresh para atualizar métricas
    if st.button("🔄 Atualizar Métricas", help="Clique para ver as métricas mais recentes"):
        st.rerun()

# Seção de alertas removida - fluxo só para com intervenção manual

# --- Helper para chamadas a webhooks (POST com fallback para GET quando necessário) ---

def call_webhook(url, payload=None, timeout=None, force_send=False):
    """
    Chama webhook sem validação automática de duplicatas.
    
    Args:
        url: URL do webhook
        payload: Dados a enviar
        timeout: Timeout da requisição
        force_send: Se True, ignora validação de duplicatas (mantido para compatibilidade)
    """
    try:
        # Apenas registrar o último número processado para histórico
        if payload and isinstance(payload, dict):
            numero = None
            for key in ['numero', 'telefone', 'phone', 'number']:
                if key in payload:
                    numero = str(payload[key])
                    break
            
            if numero:
                # Atualizar último número processado
                st.session_state["last_processed_number"] = numero
        
        # Log de tentativa de POST
        if "net_logs" in st.session_state:
            st.session_state["net_logs"].append({
                "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                "action": "POST attempt",
                "url": url,
                "payload": payload or {}
            })
        
        resp = requests.post(url, json=(payload or {}), timeout=timeout)
        
        if "net_logs" in st.session_state:
            st.session_state["net_logs"].append({
                "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                "action": "POST response",
                "status": resp.status_code,
                "text": resp.text[:500]
            })
        
        # Se o webhook estiver configurado para GET, o n8n retorna 404 com dica de método
        if resp.status_code == 404 and "Did you mean to make a GET request" in resp.text:
            if "net_logs" in st.session_state:
                st.session_state["net_logs"].append({
                    "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "GET fallback attempt",
                    "url": url,
                    "params": payload or {}
                })
            resp = requests.get(url, params=(payload or {}), timeout=timeout)
            if "net_logs" in st.session_state:
                st.session_state["net_logs"].append({
                    "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "GET fallback response",
                    "status": resp.status_code,
                    "text": resp.text[:500]
                })
        
        # Se envio foi bem-sucedido, registrar como enviado
        if resp.status_code == 200 and payload and isinstance(payload, dict):
            numero = None
            for key in ['numero', 'telefone', 'phone', 'number']:
                if key in payload:
                    numero = str(payload[key])
                    break
            
            if numero:
                message_content = payload.get('mensagem', payload.get('message', 'Mensagem enviada via webhook'))
                mark_message_as_sent(numero, message_content)
                if "net_logs" in st.session_state:
                    st.session_state["net_logs"].append({
                        "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "action": "message registered",
                        "numero": numero,
                        "message": message_content[:50] + "..." if len(message_content) > 50 else message_content
                    })
        
        return resp
    except Exception as e:
        if "net_logs" in st.session_state:
            st.session_state["net_logs"].append({
                "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                "action": "request error",
                "error": str(e)
            })
        raise e

# Status da thread do loop
if st.session_state.get("loop_active", False):
    thread_status = "🟢 Ativa" if (st.session_state.get("loop_thread") and st.session_state["loop_thread"].is_alive()) else "🔴 Inativa"
    st.info(f"🔄 **Thread do Loop**: {thread_status}")
    
    # Controle de delay entre chamadas
    col_delay1, col_delay2 = st.columns([1, 2])
    with col_delay1:
        new_delay = st.number_input(
            "Delay entre chamadas (segundos)", 
            min_value=5, 
            max_value=300, 
            value=st.session_state.get("loop_delay", 10),
            step=5,
            help="Tempo de espera entre cada chamada ao webhook"
        )
        if new_delay != st.session_state.get("loop_delay"):
            st.session_state["loop_delay"] = new_delay
            st.success(f"✅ Delay atualizado para {new_delay}s")
    with col_delay2:
        st.info(f"⏱️ Próxima chamada em até {st.session_state.get('loop_delay', 10)} segundos")

# Exibir a URL de espera gerada, se houver (mantido para compatibilidade)
if st.session_state.get("wait_url"):
    st.markdown(f"**URL do Webhook Wait para o Lead atual:** `{st.session_state['wait_url']}`")
    if st.button("🌐 Liberar Próximo"):
        try:
            with st.spinner("Liberando próximo lead..."):
                # Para liberação de fluxo, não aplicar validação de duplicata
                response = call_webhook(st.session_state["wait_url"], {"timestamp": time.time()}, force_send=True)
            if response.status_code == 200:
                st.session_state["status"] = "Liberado"
                st.session_state["wait_url"] = None
                st.success("Fluxo liberado com sucesso! Aguarde o próximo lead.")
                st.rerun()
            else:
                st.error(f"Erro ao liberar fluxo: {response.status_code} - {response.text}")
        except ReadTimeout:
            st.error("Tempo esgotado ao liberar. Configure o Webhook no n8n para responder imediatamente (Response Mode: On Received) ou aumente o timeout.")
        except ValueError as ve:
            st.error(f"Erro de validação: {ve}")
        except Exception as e:
            st.error(f"Erro ao tentar liberar o fluxo: {e}")

# --- Função do Loop Contínuo ---
def webhook_loop_runner():
    """Executa o loop contínuo chamando o webhook repetidamente, enviando apenas uma mensagem por número."""
    webhook_url = st.session_state.get("webhook_url", WEBHOOK_MAIN_URL)
    loop_delay = st.session_state.get("loop_delay", 10)  # Delay entre chamadas em segundos
    skipped_cycles = 0  # Contador de ciclos onde números já foram processados
    
    while not st.session_state.get("loop_stop_flag", False):
        try:
            # Fazer chamada ao webhook
            payload = {
                "timestamp": time.time(),
                "loop_cycle": st.session_state.get("loop_count", 0) + 1,
                "continuous_mode": True,
                "check_duplicates": True  # Sinalizar para o n8n verificar duplicatas
            }
            
            response = call_webhook(webhook_url, payload, timeout=30, force_send=True)
            
            if response.status_code == 200:
                # Incrementar contador de ciclos
                st.session_state["loop_count"] = st.session_state.get("loop_count", 0) + 1
                
                # Tentar extrair informações da resposta sobre o que foi processado
                try:
                    response_data = response.json() if response.text else {}
                    numero_processado = response_data.get("numero") or response_data.get("phone")
                    
                    if numero_processado:
                        # Verificar se o número já foi processado antes
                        if is_message_already_sent(numero_processado):
                            skipped_cycles += 1
                            # Log de número já processado
                            if "net_logs" in st.session_state:
                                st.session_state["net_logs"].append({
                                    "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "action": "loop_cycle_skipped_duplicate",
                                    "cycle": st.session_state["loop_count"],
                                    "numero": numero_processado,
                                    "status": "skipped"
                                })
                        else:
                            # Marcar número como processado
                            mark_message_as_sent(numero_processado, "Mensagem enviada via loop contínuo")
                            # Log do sucesso com novo número
                            if "net_logs" in st.session_state:
                                st.session_state["net_logs"].append({
                                    "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "action": "loop_cycle_success_new_number",
                                    "cycle": st.session_state["loop_count"],
                                    "numero": numero_processado,
                                    "status": response.status_code
                                })
                    else:
                        # Log do sucesso geral (sem número identificado)
                        if "net_logs" in st.session_state:
                            st.session_state["net_logs"].append({
                                "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                                "action": "loop_cycle_success",
                                "cycle": st.session_state["loop_count"],
                                "status": response.status_code
                            })
                            
                except:
                    # Se não conseguir parsear a resposta, apenas log do sucesso
                    if "net_logs" in st.session_state:
                        st.session_state["net_logs"].append({
                            "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "action": "loop_cycle_success",
                            "cycle": st.session_state["loop_count"],
                            "status": response.status_code
                        })
            else:
                # Log do erro
                if "net_logs" in st.session_state:
                    st.session_state["net_logs"].append({
                        "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "action": "loop_cycle_error",
                        "cycle": st.session_state.get("loop_count", 0),
                        "status": response.status_code,
                        "error": response.text[:200]
                    })
            
            # Atualizar contador de ciclos pulados
            st.session_state["skipped_cycles"] = skipped_cycles
            
            # Aguardar antes da próxima chamada (se não foi solicitada parada)
            for i in range(loop_delay):
                if st.session_state.get("loop_stop_flag", False):
                    break
                time.sleep(1)
                
        except Exception as e:
            # Log do erro de exceção
            if "net_logs" in st.session_state:
                st.session_state["net_logs"].append({
                    "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "action": "loop_exception",
                    "error": str(e)
                })
            
            # Aguardar antes de tentar novamente
            for i in range(5):  # Aguarda 5 segundos em caso de erro
                if st.session_state.get("loop_stop_flag", False):
                    break
                time.sleep(1)
    
    # Loop foi parado
    st.session_state["loop_active"] = False
    if "net_logs" in st.session_state:
        st.session_state["net_logs"].append({
            "when": time.strftime("%Y-%m-%d %H:%M:%S"),
            "action": "loop_stopped",
            "total_cycles": st.session_state.get("loop_count", 0),
            "skipped_cycles": skipped_cycles,
            "unique_numbers": len(st.session_state.get("message_history", {}))
        })

# --- Funções de Validação e Controle ---
def normalize_phone_number(phone):
    """Normaliza número de telefone para formato padrão."""
    if not phone:
        return None
    
    # Remove tudo que não for dígito
    digits_only = ''.join(filter(str.isdigit, str(phone)))
    
    # Garante que comece com 55 (Brasil)
    if not digits_only.startswith('55'):
        digits_only = '55' + digits_only
    
    return digits_only

def is_message_already_sent(phone_number):
    """Verifica se mensagem já foi enviada para este número."""
    normalized_phone = normalize_phone_number(phone_number)
    if not normalized_phone:
        return False
    
    # Verificar no histórico de mensagens
    if normalized_phone in st.session_state.get("message_history", {}):
        message_info = st.session_state["message_history"][normalized_phone]
        return message_info.get("status") == "sent"
    
    # Verificar na lista de números processados (compatibilidade)
    return normalized_phone in st.session_state.get("processed_numbers", set())

def mark_message_as_sent(phone_number, message_content=""):
    """Marca mensagem como enviada para um número."""
    normalized_phone = normalize_phone_number(phone_number)
    if not normalized_phone:
        return False
    
    # Adicionar ao histórico detalhado
    st.session_state["message_history"][normalized_phone] = {
        "timestamp": time.time(),
        "status": "sent",
        "message": message_content,
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Manter compatibilidade com lista antiga
    st.session_state["processed_numbers"].add(normalized_phone)
    return True

def validate_api_key(api_key):
    """Valida se a API Key está funcionando corretamente."""
    try:
        base_url = st.session_state.get("webhook_url", WEBHOOK_MAIN_URL).split("/webhook")[0]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Testar com endpoint simples de workflows
        response = requests.get(f"{base_url}/rest/workflows", headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, "API Key válida"
        elif response.status_code == 401:
            return False, "API Key inválida ou expirada"
        else:
            return False, f"Erro de conexão: {response.status_code}"
            
    except Exception as e:
        return False, f"Erro ao validar API Key: {e}"

def emergency_stop_workflow():
    """Para o workflow imediatamente em caso de emergência."""
    try:
        api_key = st.session_state.get("n8n_api_key") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NWM4YTg2Zi1iZDc3LTRjZTYtYjJmYS1mM2Q3MGZhNzJkOWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU3MzUyODYxfQ.2RTE1LNNfX2VIImn3Obncd0f_MnOBap7qJzeb2gwo_c"
        workflow_id = st.session_state.get("workflow_id") or WORKFLOW_ID
        
        # Validar API Key primeiro
        is_valid, message = validate_api_key(api_key)
        if not is_valid:
            st.error(f"❌ Problema com API Key: {message}")
            st.warning("💡 Gere uma nova API Key no n8n: Settings > n8n API > Personal Access Token")
            return False
        
        if api_key and workflow_id:
            # Desativar workflow
            success = activate_workflow(workflow_id, api_key, activate=False)
            if success:
                st.session_state["status"] = "Parado - Emergência"
                st.session_state["wait_url"] = None
                st.session_state["current_lead"] = None
                return True
        return False
    except Exception as e:
        st.error(f"Erro ao parar workflow de emergência: {e}")
        return False

def clean_duplicate_history():
    """Remove duplicatas do histórico mantendo apenas a entrada mais recente."""
    message_history = st.session_state.get("message_history", {})
    processed_numbers = st.session_state.get("processed_numbers", set())
    
    # Verificar inconsistências entre as duas estruturas
    cleaned_count = 0
    
    # Remover números do processed_numbers que não estão no message_history
    to_remove = []
    for num in processed_numbers:
        if num not in message_history:
            to_remove.append(num)
    
    for num in to_remove:
        processed_numbers.remove(num)
        cleaned_count += 1
    
    # Adicionar números do message_history que não estão no processed_numbers
    for num in message_history:
        if message_history[num].get("status") == "sent":
            processed_numbers.add(num)
    
    st.session_state["processed_numbers"] = processed_numbers
    st.session_state["message_history"] = message_history
    
    return cleaned_count

def load_leads_data():
    """Carrega dados dos leads do arquivo JSON."""
    try:
        leads_file = "/Users/guilhermemoreno/Desktop/FrontEnd-N8N/Leads sdr AMAC - FUNCIONANDO copy (1).json"
        with open(leads_file, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        # Procurar por dados de leads nos nodes
        leads = []
        for node in workflow_data.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.code" and "empresas" in node.get("parameters", {}).get("jsCode", ""):
                # Este é provavelmente o node que processa os dados dos leads
                st.info("📊 Estrutura de dados dos leads detectada no workflow")
                break
        
        return leads
    except Exception as e:
        st.warning(f"Não foi possível carregar dados dos leads: {e}")
        return []

# --- Funções do Fluxo de Trabalho ---
def check_workflow_status():
    """Verifica se o workflow está ativo no n8n."""
    api_key = st.session_state.get("n8n_api_key") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NWM4YTg2Zi1iZDc3LTRjZTYtYjJmYS1mM2Q3MGZhNzJkOWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU3MzUyODYxfQ.2RTE1LNNfX2VIImn3Obncd0f_MnOBap7qJzeb2gwo_c"
    workflow_id = st.session_state.get("workflow_id") or WORKFLOW_ID
    
    try:
        # Extrair base URL do webhook
        base_url = st.session_state.get("webhook_url", WEBHOOK_MAIN_URL).split("/webhook")[0]
        api_url = f"{base_url}/rest/workflows/{workflow_id}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            workflow_data = response.json()
            is_active = workflow_data.get("active", False)
            return is_active, f"Workflow está {'ativo' if is_active else 'inativo'}"
        elif response.status_code == 401:
            return None, "Erro de autenticação - API Key inválida ou expirada"
        elif response.status_code == 404:
            return None, f"Workflow ID '{workflow_id}' não encontrado"
        else:
            return None, f"Erro ao verificar status: {response.status_code}"
            
    except Exception as e:
        return None, f"Erro ao conectar com n8n API: {e}"

def iniciar_fluxo():
    """Inicia o fluxo de trabalho do n8n em loop contínuo."""
    if st.session_state["status"] == "Em Execução":
        st.warning("Fluxo já está em execução!")
        return
    
    # Usar API Key padrão se não estiver configurada
    api_key = st.session_state.get("n8n_api_key") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NWM4YTg2Zi1iZDc3LTRjZTYtYjJmYS1mM2Q3MGZhNzJkOWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU3MzUyODYxfQ.2RTE1LNNfX2VIImn3Obncd0f_MnOBap7qJzeb2gwo_c"
    workflow_id = st.session_state.get("workflow_id") or WORKFLOW_ID
    
    # Tentar encontrar workflow_id automaticamente se não estiver configurado
    if not workflow_id and api_key:
        try:
            base_url = st.session_state.get("webhook_url", WEBHOOK_MAIN_URL).split("/webhook")[0]
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(f"{base_url}/rest/workflows", headers=headers, timeout=10)
            
            if response.status_code == 200:
                workflows = response.json()["data"]
                # Procurar workflow que contenha o webhook ID
                webhook_id = WEBHOOK_MAIN_URL.split("/")[-1]  # ce723d0d-a280-414f-aec3-85c940f7dc6f
                
                for wf in workflows:
                    # Buscar nos nodes do workflow
                    nodes = wf.get("nodes", [])
                    for node in nodes:
                        if (node.get("type") == "n8n-nodes-base.webhook" and 
                            node.get("webhookId") == webhook_id):
                            workflow_id = str(wf["id"])
                            st.session_state["workflow_id"] = workflow_id
                            st.info(f"🔍 Workflow ID detectado automaticamente: {workflow_id}")
                            break
                    if workflow_id:
                        break
        except Exception as e:
            st.warning(f"Não foi possível detectar o Workflow ID automaticamente: {e}")
    
    # Verificar e ativar workflow se necessário
    if api_key and workflow_id:
        is_active, message = check_workflow_status()
        if is_active is False:
            st.warning("⚠️ Workflow está inativo. Tentando ativar automaticamente...")
            success = activate_workflow(workflow_id, api_key, activate=True)
            if not success:
                st.error("❌ **Não foi possível ativar o workflow automaticamente!**")
                st.markdown("""
                **Ative manualmente:**
                1. 🔗 Acesse: https://projeto01-n8n.peitvn.easypanel.host
                2. 📝 Abra o workflow que contém este webhook
                3. 🔄 **Ative o workflow** usando o toggle no canto superior direito
                4. ✅ Tente iniciar o fluxo novamente
                """)
                return
        elif is_active is True:
            st.info("✅ Workflow confirmado como ativo. Iniciando loop contínuo...")
        
    # Parar thread anterior se existir
    if st.session_state.get("loop_thread") and st.session_state["loop_thread"].is_alive():
        st.warning("⚠️ Parando loop anterior...")
        st.session_state["loop_stop_flag"] = True
        st.session_state["loop_thread"].join(timeout=5)
    
    # Configurar novo loop
    st.session_state["status"] = "Em Execução"
    st.session_state["execution_start_time"] = time.time()
    st.session_state["loop_active"] = True
    st.session_state["loop_count"] = 0
    st.session_state["skipped_cycles"] = 0
    st.session_state["loop_stop_flag"] = False
    
    st.success("🔄 **Iniciando LOOP CONTÍNUO COM CONTROLE DE DUPLICATAS!**")
    st.info("💡 O sistema vai chamar o webhook n8n repetidamente, mas enviará apenas UMA mensagem por número")
    st.info("🛡️ Números já processados serão pulados automaticamente, mantendo o loop ativo")
    
    # Iniciar thread do loop em background
    try:
        loop_thread = threading.Thread(target=webhook_loop_runner, daemon=True)
        loop_thread.start()
        st.session_state["loop_thread"] = loop_thread
        
        st.success("✅ **Loop contínuo iniciado com sucesso!**")
        st.info("🔄 O webhook está sendo chamado automaticamente em background")
        st.info("📊 Acompanhe o progresso nas métricas acima")
        
    except Exception as e:
        st.session_state["status"] = "Erro"
        st.session_state["loop_active"] = False
        st.error(f"Erro ao iniciar thread do loop: {e}")

def activate_workflow(workflow_id, api_key, activate=True):
    """Ativa ou desativa um workflow no n8n."""
    try:
        # Extrair base URL do webhook
        base_url = st.session_state.get("webhook_url", WEBHOOK_MAIN_URL).split("/webhook")[0]
        api_url = f"{base_url}/rest/workflows/{workflow_id}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        action = "Ativando" if activate else "Desativando"
        with st.spinner(f"{action} workflow no n8n..."):
            response = requests.patch(api_url, json={"active": activate}, headers=headers, timeout=15)
        
        if response.status_code == 200:
            status = "ativado" if activate else "desativado"
            st.success(f"✅ Workflow {status} no n8n!")
            return True
        elif response.status_code == 401:
            st.error("❌ **Erro de Autenticação (401 Unauthorized)**")
            st.markdown("""
            **🔑 Problema com a API Key:**
            
            **Possíveis causas:**
            - API Key expirada ou inválida
            - Permissões insuficientes
            - Token malformado
            
            **💡 Solução:**
            1. 🔗 Acesse: https://projeto01-n8n.peitvn.easypanel.host
            2. ⚙️ Vá em **Settings** > **n8n API** > **Personal Access Token**
            3. 🗑️ **Delete** o token antigo (se existir)
            4. ➕ **Crie um novo token**
            5. 📋 **Copie** e **cole** no campo "API Key do n8n" abaixo
            """)
            return False
        elif response.status_code == 404:
            st.error(f"❌ **Workflow não encontrado (404)**")
            st.warning(f"⚠️ Workflow ID '{workflow_id}' não existe ou você não tem acesso a ele")
            return False
        else:
            st.error(f"❌ Erro ao {action.lower()} workflow: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        action = "ativar" if activate else "desativar"
        st.error(f"❌ Erro ao {action} workflow: {e}")
        return False

def parar_fluxo():
    """Interrompe o loop contínuo do fluxo de trabalho."""
    if st.session_state["status"] == "Parado":
        st.info("Fluxo já está parado.")
        return
    
    # Parar o loop contínuo primeiro
    if st.session_state.get("loop_active", False):
        st.info("🛑 Parando loop contínuo...")
        
        # Sinalizar para a thread parar
        st.session_state["loop_stop_flag"] = True
        
        # Aguardar thread terminar
        if st.session_state.get("loop_thread") and st.session_state["loop_thread"].is_alive():
            with st.spinner("Aguardando thread do loop parar..."):
                st.session_state["loop_thread"].join(timeout=10)
            
            if st.session_state["loop_thread"].is_alive():
                st.warning("⚠️ Thread do loop não parou completamente, mas foi sinalizada para parar")
            else:
                st.success("✅ Thread do loop parada com sucesso!")
    
    # Usar API Key padrão se não estiver configurada
    api_key = st.session_state.get("n8n_api_key") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NWM4YTg2Zi1iZDc3LTRjZTYtYjJmYS1mM2Q3MGZhNzJkOWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU3MzUyODYxfQ.2RTE1LNNfX2VIImn3Obncd0f_MnOBap7qJzeb2gwo_c"
    workflow_id = st.session_state.get("workflow_id") or WORKFLOW_ID
    
    # Tentar encontrar workflow_id automaticamente se não estiver configurado
    if not workflow_id:
        # Extrair do webhook URL se possível
        webhook_url = st.session_state.get("webhook_url", WEBHOOK_MAIN_URL)
        if "/webhook/" in webhook_url:
            # Tentar buscar workflows ativos
            try:
                base_url = webhook_url.split("/webhook")[0]
                headers = {"Authorization": f"Bearer {api_key}"}
                response = requests.get(f"{base_url}/rest/workflows", headers=headers, timeout=10)
                
                if response.status_code == 200:
                    workflows = response.json()["data"]
                    # Procurar workflow ativo que contenha webhook
                    for wf in workflows:
                        if wf.get("active", False):
                            workflow_id = str(wf["id"])
                            st.session_state["workflow_id"] = workflow_id
                            st.info(f"🔍 Workflow ID detectado automaticamente: {workflow_id}")
                            break
            except Exception as e:
                st.warning(f"Não foi possível detectar o Workflow ID automaticamente: {e}")
    
    if api_key and workflow_id:
        success = activate_workflow(workflow_id, api_key, activate=False)
        if not success:
            st.warning("⚠️ Workflow pode ainda estar ativo no n8n. Desative manualmente se necessário.")
    else:
        st.info("💡 Configure Workflow ID para desativar automaticamente no n8n")
        
    # Parar localmente e limpar estado do loop
    st.session_state["status"] = "Parado"
    st.session_state["wait_url"] = None
    st.session_state["current_lead"] = None
    st.session_state["loop_active"] = False
    
    # Mostrar estatísticas do loop
    loop_count = st.session_state.get("loop_count", 0)
    if loop_count > 0:
        st.info(f"🔄 Loop executou {loop_count} ciclos antes de parar")
    
    # Limpar execução ativa
    if "execution_start_time" in st.session_state:
        execution_time = time.time() - st.session_state["execution_start_time"]
        st.success(f"🛑 **Loop contínuo parado!** Executou por {execution_time:.1f} segundos.")
        del st.session_state["execution_start_time"]
    else:
        st.success("🛑 **Loop contínuo parado manualmente pelo usuário!**")

# --- Seção de Controle do App ---
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("▶ Iniciar Fluxo"):
        iniciar_fluxo()

with col2:
    if st.button("◼ Parar Fluxo"):
        parar_fluxo()

with col3:
    if st.button("🚨 PARADA DE EMERGÊNCIA", type="secondary"):
        st.warning("⚠️ Executando parada de emergência...")
        if emergency_stop_workflow():
            st.success("✅ Workflow parado em emergência!")
            st.session_state["status"] = "Parado - Emergência"
        else:
            st.error("❌ Falha na parada de emergência! Desative manualmente no n8n!")
        st.rerun()

st.divider()

# Informações sobre o modo de operação
if st.session_state.get("loop_active", False):
    st.info("🔄 **LOOP REAL ATIVO** - Sistema chamando webhook automaticamente em background")
    st.success("✅ Para parar o loop, use o botão 'Parar Fluxo' acima")
    
    # Mostrar últimos logs do loop
    logs = st.session_state.get("net_logs", [])
    loop_logs = [log for log in logs[-5:] if "loop" in log.get("action", "")]
    if loop_logs:
        with st.expander("📋 Últimos eventos do loop"):
            for log in loop_logs:
                st.write(f"**{log['when']}** - {log['action']}: {log.get('cycle', 'N/A')}")
else:
    st.info("🔄 **MODO LOOP INTELIGENTE** - Clique em 'Iniciar Fluxo' para processar leads continuamente")
    st.success("✨ **Funcionalidade**: Loop contínuo + Controle de duplicatas automático")
    st.info("🛡️ Sistema envia apenas UMA mensagem por número, pulando duplicatas automaticamente")

st.info("📊 A seção de análise foi movida para a página 'Dashboard' no menu lateral.")

# --- Configuração e Diagnóstico ---
# Estado inicial para URL e logs
if "webhook_url" not in st.session_state:
    st.session_state["webhook_url"] = WEBHOOK_MAIN_URL
if "net_logs" not in st.session_state:
    st.session_state["net_logs"] = []

with st.expander("⚙️ Configuração e Diagnóstico do Webhook", expanded=False):
    st.caption("Defina a URL e teste manualmente o envio para verificar conectividade.")
    
    # Configurações do Webhook
    st.session_state["webhook_url"] = st.text_input(
        "Webhook URL",
        value=st.session_state.get("webhook_url", WEBHOOK_MAIN_URL),
        help="Cole aqui a Production URL do node Webhook no n8n."
    )
    
    # Configurações da API do n8n
    st.markdown("**Configuração da API do n8n (para controle avançado):**")
    col_api1, col_api2, col_api3 = st.columns([2,2,1])
    with col_api1:
        st.session_state["n8n_api_key"] = st.text_input(
            "API Key do n8n",
            value=st.session_state.get("n8n_api_key", ""),
            type="password",
            help="Gere em: Settings > n8n API > Personal Access Token"
        )
    with col_api2:
        st.session_state["workflow_id"] = st.text_input(
            "Workflow ID",
            value=st.session_state.get("workflow_id", WORKFLOW_ID),
            help="ID do workflow (visível na URL quando edita o workflow)"
        )
    with col_api3:
        if st.button("🔍 Verificar Status"):
            is_active, message = check_workflow_status()
            if is_active is True:
                st.success(f"✅ {message}")
            elif is_active is False:
                st.error(f"❌ {message}")
                st.warning("⚠️ Ative o workflow no n8n antes de iniciar o fluxo!")
            else:
                st.info(f"ℹ️ {message}")
    
    # Histórico de mensagens (apenas para controle visual)
    st.markdown("**📊 Histórico de Mensagens:**")
    st.info("💡 O fluxo agora roda continuamente até ser parado manualmente pelo usuário.")
    
    # Controles manuais de ativação/desativação
    if st.session_state.get("workflow_id"):
        st.markdown("**Controle Manual do Workflow:**")
        col_ctrl1, col_ctrl2 = st.columns(2)
        with col_ctrl1:
            if st.button("🟢 Ativar Workflow"):
                api_key = st.session_state.get("n8n_api_key") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NWM4YTg2Zi1iZDc3LTRjZTYtYjJmYS1mM2Q3MGZhNzJkOWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU3MzUyODYxfQ.2RTE1LNNfX2VIImn3Obncd0f_MnOBap7qJzeb2gwo_c"
                activate_workflow(st.session_state["workflow_id"], api_key, activate=True)
        with col_ctrl2:
            if st.button("🔴 Desativar Workflow"):
                api_key = st.session_state.get("n8n_api_key") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NWM4YTg2Zi1iZDc3LTRjZTYtYjJmYS1mM2Q3MGZhNzJkOWMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzU3MzUyODYxfQ.2RTE1LNNfX2VIImn3Obncd0f_MnOBap7qJzeb2gwo_c"
                activate_workflow(st.session_state["workflow_id"], api_key, activate=False)
    
    # Controle de números únicos e histórico de mensagens
    st.markdown("**Controle de Mensagens Enviadas:**")
    
    # Métricas
    col_metric1, col_metric2, col_metric3 = st.columns(3)
    with col_metric1:
        total_processed = len(st.session_state.get("processed_numbers", set()))
        st.metric("Total Processados", total_processed)
    with col_metric2:
        message_history = st.session_state.get("message_history", {})
        total_sent = len([m for m in message_history.values() if m.get("status") == "sent"])
        st.metric("Mensagens Enviadas", total_sent)
    with col_metric3:
        if message_history:
            last_sent = max(message_history.values(), key=lambda x: x.get("timestamp", 0))
            last_date = last_sent.get("date", "Nunca")
            st.metric("Última Mensagem", last_date)
        else:
            st.metric("Última Mensagem", "Nunca")
    
    # Controles
    col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4, col_ctrl5 = st.columns(5)
    with col_ctrl1:
        if st.button("📋 Ver Histórico"):
            message_history = st.session_state.get("message_history", {})
            if message_history:
                st.markdown("**📋 Histórico de Mensagens:**")
                for phone, info in sorted(message_history.items(), key=lambda x: x[1].get("timestamp", 0), reverse=True)[:10]:
                    status_icon = "✅" if info.get("status") == "sent" else "❌"
                    st.write(f"{status_icon} **{phone}** - {info.get('date', 'Data desconhecida')}")
                    if info.get("message"):
                        st.caption(f"Mensagem: {info['message'][:50]}...")
                if len(message_history) > 10:
                    st.caption(f"... e mais {len(message_history) - 10} mensagens")
            else:
                st.info("Nenhuma mensagem enviada ainda")
                
    with col_ctrl2:
        if st.button("📊 Ver Lista Simples"):
            numbers = list(st.session_state.get("processed_numbers", set()))
            if numbers:
                st.write("**Números processados:**", numbers[:20])
                if len(numbers) > 20:
                    st.caption(f"... e mais {len(numbers) - 20} números")
            else:
                st.info("Nenhum número processado ainda")
                
    with col_ctrl3:
        if st.button("🔍 Verificar Número"):
            check_number = st.text_input("Digite o número para verificar:", key="check_number_input")
            if check_number:
                if is_message_already_sent(check_number):
                    normalized = normalize_phone_number(check_number)
                    message_info = st.session_state.get("message_history", {}).get(normalized, {})
                    st.error(f"❌ Mensagem já foi enviada para {check_number}")
                    if message_info:
                        st.info(f"📅 Data: {message_info.get('date', 'Desconhecida')}")
                        if message_info.get("message"):
                            st.info(f"💬 Mensagem: {message_info['message'][:100]}...")
                else:
                    st.success(f"✅ Número {check_number} ainda não recebeu mensagem")
                    
    with col_ctrl4:
        if st.button("🔧 Limpar Duplicatas"):
            cleaned = clean_duplicate_history()
            if cleaned > 0:
                st.success(f"🔧 {cleaned} inconsistências corrigidas!")
            else:
                st.info("✅ Histórico já está consistente")
            st.rerun()
            
    with col_ctrl5:
        if st.button("🗑️ Limpar Histórico"):
            st.session_state["processed_numbers"] = set()
            st.session_state["message_history"] = {}
            st.success("Histórico limpo!")
            st.rerun()

    st.markdown("**🔧 Diagnóstico de Conectividade:**")
    
    # Verificação automática do workflow
    col_diag1, col_diag2 = st.columns(2)
    with col_diag1:
        if st.button("🔍 Verificar Status do Workflow"):
            is_active, message = check_workflow_status()
            if is_active is True:
                st.success(f"✅ {message}")
            elif is_active is False:
                st.error(f"❌ {message}")
                st.markdown("""
                **🔧 Para ativar o workflow:**
                1. 🔗 Acesse: https://projeto01-n8n.peitvn.easypanel.host
                2. 📝 Abra o workflow
                3. 🔄 Clique no toggle "Active" no canto superior direito
                """)
            else:
                st.warning(f"⚠️ {message}")
    
    with col_diag2:
        if st.button("🌐 Testar Conectividade Básica"):
            try:
                with st.spinner("Testando conectividade..."):
                    import urllib.parse
                    base_url = st.session_state.get("webhook_url", WEBHOOK_MAIN_URL).split("/webhook")[0]
                    response = requests.get(base_url, timeout=10)
                if response.status_code == 200:
                    st.success("✅ Servidor n8n acessível")
                else:
                    st.warning(f"⚠️ Servidor respondeu com status: {response.status_code}")
            except Exception as e:
                st.error(f"❌ Erro de conectividade: {e}")
    
    col_test1, col_test2, col_test3 = st.columns([1,1,1])
    with col_test1:
        timeout_val = st.number_input("Timeout (s)", min_value=5, max_value=120, value=30, step=5)
    with col_test2:
        run_post = st.button("🧪 Testar POST")
    with col_test3:
        run_get = st.button("🧪 Testar GET")

    st.markdown("**🚨 Troubleshooting - Webhook não responde:**")
    with st.expander("🔧 Principais causas e soluções"):
        st.markdown("""
        **1. ❌ Workflow inativo no n8n**
        - ✅ Solução: Acesse o n8n e ative o workflow (toggle "Active")
        
        **2. 🔗 URL do webhook incorreta**
        - ✅ Solução: Copie a Production URL do node Webhook no n8n
        
        **3. 🚫 Servidor n8n offline**
        - ✅ Solução: Verifique se https://projeto01-n8n.peitvn.easypanel.host está acessível
        
        **4. ⚙️ Configuração do node Webhook**
        - ✅ Verifique se está configurado como POST
        - ✅ Verifique se "Respond" está ativo
        - ✅ Verifique se "Response Mode" está correto
        
        **5. 🔑 Problemas de autenticação**
        - ✅ Verifique se o workflow não tem autenticação extra
        
        **6. 🌐 Problemas de rede**
        - ✅ Teste a conectividade básica acima
        """)
    
    st.info("💡 **Dica**: Use os botões de diagnóstico acima para identificar o problema específico.")
    
    # Status de execução
    if "execution_start_time" in st.session_state:
        runtime = time.time() - st.session_state["execution_start_time"]
        st.metric("Tempo de execução", f"{runtime:.1f}s")
    
    if st.session_state["status"] == "Em Execução":
        st.success("🟢 Fluxo ativo no Python")
    elif st.session_state["status"] == "Parado":
        st.info("⚪ Fluxo inativo")
    elif st.session_state["status"] == "Erro":
        st.error("🔴 Último disparo falhou")

    default_payload = {"timestamp": time.time(), "numero": "5511999999999"}
    payload_text = st.text_area("Payload (JSON)", value=json.dumps(default_payload, ensure_ascii=False))

    test_payload = None
    try:
        test_payload = json.loads(payload_text) if payload_text.strip() else {}
    except Exception as e:
        st.error(f"JSON inválido no payload de teste: {e}")

    if run_post and test_payload is not None:
        try:
            # Identificar número no payload apenas para logs
            numero = None
            for key in ['numero', 'telefone', 'phone', 'number']:
                if key in test_payload:
                    numero = str(test_payload[key])
                    break
            
            st.info(f"🔗 **URL de destino**: {st.session_state['webhook_url']}")
            st.info(f"📦 **Payload**: {json.dumps(test_payload, indent=2)}")
            
            # Enviar sem validação de duplicatas
            with st.spinner("Enviando POST de teste..."):
                start_time = time.time()
                r = call_webhook(
                    st.session_state["webhook_url"], 
                    test_payload, 
                    timeout=int(timeout_val),
                    force_send=True  # Sempre forçar envio em testes
                )
                response_time = time.time() - start_time
            
            # Análise detalhada da resposta
            st.write(f"**⏱️ Tempo de resposta**: {response_time:.2f}s")
            st.write(f"**📊 Status HTTP**: {r.status_code}")
            
            if r.status_code == 200:
                st.success("✅ **Webhook respondeu com sucesso!**")
                if numero:
                    st.info(f"📱 Número {numero} registrado no histórico")
            elif r.status_code == 404:
                st.error("❌ **Webhook não encontrado (404)**")
                st.markdown("""
                **Possíveis causas:**
                - Workflow não está ativo no n8n
                - URL do webhook está incorreta
                - Webhook foi deletado ou modificado
                """)
            elif r.status_code == 500:
                st.error("❌ **Erro interno do servidor (500)**")
                st.warning("Pode haver um erro no workflow n8n")
            else:
                st.warning(f"⚠️ **Status inesperado**: {r.status_code}")
            
            # Mostrar resposta detalhada
            if r.text:
                st.markdown("**📄 Resposta do servidor:**")
                st.code(r.text[:1000])
            else:
                st.info("📄 Servidor não retornou conteúdo")
            
            # Mostrar headers de resposta
            if r.headers:
                with st.expander("🔍 Headers de resposta"):
                    for key, value in r.headers.items():
                        st.write(f"**{key}**: {value}")
            
        except requests.exceptions.ConnectTimeout:
            st.error("❌ **Timeout de conexão**")
            st.warning("O servidor n8n não está respondendo")
        except requests.exceptions.ReadTimeout:
            st.error("❌ **Timeout de leitura**")
            st.warning("O webhook demorou muito para responder")
        except requests.exceptions.ConnectionError:
            st.error("❌ **Erro de conexão**")
            st.warning("Não foi possível conectar ao servidor n8n")
        except Exception as e:
            st.error(f"❌ **Erro no POST de teste**: {e}")
            st.info("💡 Verifique se o n8n está rodando e o workflow está ativo")

    if run_get and test_payload is not None:
        try:
            with st.spinner("Enviando GET de teste..."):
                r = requests.get(st.session_state["webhook_url"], params=test_payload, timeout=int(timeout_val))
            st.write(f"Status: {r.status_code}")
            st.code((r.text or "" )[:1000])
        except Exception as e:
            st.error(f"Erro no GET de teste: {e}")

    st.markdown("---")
    st.caption("Últimos eventos de rede (limite de 10):")
    logs = st.session_state.get("net_logs", [])[-10:]
    for item in logs:
        st.write(item)