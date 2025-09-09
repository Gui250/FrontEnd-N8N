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
def normalize_phone_number(phone):
    """Normaliza número de telefone para formato padrão."""
    if not phone:
        return None
    digits_only = ''.join(filter(str.isdigit, str(phone)))
    if not digits_only.startswith('55'):
        digits_only = '55' + digits_only
    return digits_only

def is_message_already_sent(phone_number):
    """Verifica se mensagem já foi enviada para este número."""
    normalized_phone = normalize_phone_number(phone_number)
    if not normalized_phone:
        return False
    return normalized_phone in st.session_state.get("message_history", {})

def mark_message_as_sent(phone_number, message_content=""):
    """Marca mensagem como enviada para um número."""
    normalized_phone = normalize_phone_number(phone_number)
    if not normalized_phone:
        return False
    
    st.session_state["message_history"][normalized_phone] = {
        "timestamp": time.time(),
        "status": "sent",
        "message": message_content,
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    return True

def load_leads_numbers():
    """Carrega números dos leads do arquivo JSON."""
    try:
        leads_file = "/Users/guilhermemoreno/Desktop/FrontEnd-N8N/Leads sdr AMAC - FUNCIONANDO copy (1).json"
        with open(leads_file, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)
        
        numbers = []
        for node in workflow_data.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.code":
                js_code = node.get("parameters", {}).get("jsCode", "")
                patterns = [r'55\d{10,11}', r'\d{10,11}', r'5511\d{8,9}']
                
                for pattern in patterns:
                    found_numbers = re.findall(pattern, js_code)
                    for num in found_numbers:
                        if len(num) >= 10:
                            normalized = normalize_phone_number(num)
                            if normalized and normalized not in numbers:
                                numbers.append(normalized)
        
        # Fallback para números de exemplo
        if not numbers:
            base_numbers = ["5511999999", "5511888888", "5521999999", "5531999999"]
            for base in base_numbers:
                for i in range(100, 200):
                    numbers.append(f"{base}{i:03d}")
        
        st.session_state["leads_numbers"] = numbers
        return numbers
        
    except Exception as e:
        # Fallback para números sequenciais
        example_numbers = [f"5511999{i:06d}" for i in range(1000, 2000)]
        st.session_state["leads_numbers"] = example_numbers
        return example_numbers

def get_next_dynamic_number():
    """Retorna o próximo número dinâmico - SEMPRE gera um número válido."""
    mode = st.session_state.get("number_generation_mode", "real_leads")
    
    # MODO 1: Números reais dos leads
    if mode == "real_leads":
        if not st.session_state.get("leads_numbers"):
            load_leads_numbers()
        
        numbers = st.session_state.get("leads_numbers", [])
        if numbers:
            # Encontrar próximo número não enviado
            for i in range(len(numbers)):
                current_index = st.session_state.get("current_number_index", 0)
                if current_index >= len(numbers):
                    # Se chegou ao fim, usar modo sequencial como fallback
                    break
                
                number = numbers[current_index]
                st.session_state["current_number_index"] = current_index + 1
                
                if not is_message_already_sent(number):
                    return number
    
    # MODO 2: Números aleatórios (sempre únicos)
    elif mode == "random":
        # Gerar número baseado em timestamp para garantir unicidade
        timestamp_part = int(time.time() * 1000) % 100000000  # 8 dígitos
        area_codes = ["11", "21", "31", "41", "51"]
        area = random.choice(area_codes)
        return f"55{area}9{timestamp_part}"
    
    # MODO 3: Números sequenciais
    elif mode == "sequential":
        current_index = st.session_state.get("current_number_index", 0)
        st.session_state["current_number_index"] = current_index + 1
        return f"5511999{current_index:06d}"
    
    # FALLBACK: Sempre retorna um número único baseado em timestamp
    unique_part = int(time.time() * 1000) % 1000000
    return f"5511999{unique_part:06d}"

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

def execute_single_loop_cycle():
    """Executa um único ciclo do loop."""
    try:
        if st.session_state.get("loop_stop_flag", False):
            return False
        
        # Gerar número dinâmico - SEMPRE funciona
        dynamic_number = get_next_dynamic_number()
        
        # Preparar payload
        payload = {
            "timestamp": time.time(),
            "numero": dynamic_number,
            "loop_cycle": st.session_state.get("loop_count", 0) + 1,
            "continuous_mode": True
        }
        
        # Log detalhado do que está sendo enviado
        st.session_state["net_logs"].append({
            "when": time.strftime("%H:%M:%S"),
            "action": "SENDING",
            "numero": dynamic_number,
            "cycle": payload["loop_cycle"]
        })
        
        # Chamar webhook
        response = call_webhook(st.session_state["webhook_url"], payload)
        
        # Sempre incrementar contador (mesmo se der erro)
        st.session_state["loop_count"] += 1
        
        if response.status_code == 200:
            # Marcar como enviado apenas se sucesso
            mark_message_as_sent(dynamic_number, "Mensagem enviada via loop")
            st.session_state["net_logs"].append({
                "when": time.strftime("%H:%M:%S"),
                "action": "SUCCESS",
                "numero": dynamic_number,
                "status": response.status_code
            })
        else:
            # Log de erro mas continua
            st.session_state["net_logs"].append({
                "when": time.strftime("%H:%M:%S"),
                "action": "ERROR",
                "numero": dynamic_number,
                "status": response.status_code,
                "error": response.text[:100]
            })
        
        return True  # SEMPRE continuar
            
    except Exception as e:
        # Log de exceção mas continua
        st.session_state["net_logs"].append({
            "when": time.strftime("%H:%M:%S"),
            "action": "EXCEPTION",
            "error": str(e)
        })
        return True  # SEMPRE continuar

# --- Interface Principal ---
st.write(f"📌 **Status atual:** {st.session_state['status']}")

# Métricas do loop
if st.session_state.get("loop_active", False):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔄 Status", "ATIVO", delta="Loop executando")
    with col2:
        st.metric("📊 Ciclos", st.session_state.get("loop_count", 0))
    with col3:
        unique_numbers = len(st.session_state.get("message_history", {}))
        st.metric("📱 Números Únicos", unique_numbers)
    with col4:
        if st.session_state.get("execution_start_time"):
            runtime = time.time() - st.session_state["execution_start_time"]
            st.metric("⏱️ Tempo", f"{runtime:.0f}s")
        else:
            st.metric("⏱️ Tempo", "0s")
    
    st.success("🟢 **Loop ativo** - Enviando mensagens para números únicos")
    
    # Controle de delay
    col_delay1, col_delay2 = st.columns([1, 2])
    with col_delay1:
        new_delay = st.number_input(
            "Intervalo (segundos)", 
            min_value=5, 
            max_value=60, 
            value=st.session_state.get("loop_delay", 10),
            step=5
        )
        if new_delay != st.session_state.get("loop_delay"):
            st.session_state["loop_delay"] = new_delay
    with col_delay2:
        current_time = time.time()
        last_execution = st.session_state.get("last_loop_execution", 0)
        remaining = max(0, st.session_state["loop_delay"] - (current_time - last_execution))
        st.info(f"⏳ Próximo ciclo em {remaining:.1f}s")

# Botões de controle
st.divider()
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("▶️ Iniciar Loop", type="primary", disabled=st.session_state.get("loop_active", False)):
        st.session_state["status"] = "Em Execução"
        st.session_state["loop_active"] = True
        st.session_state["loop_count"] = 0
        st.session_state["execution_start_time"] = time.time()
        st.session_state["last_loop_execution"] = 0
        st.session_state["loop_stop_flag"] = False
        st.success("🚀 Loop iniciado!")
        st.rerun()

with col2:
    if st.button("⏹️ Parar Loop", disabled=not st.session_state.get("loop_active", False)):
        st.session_state["loop_active"] = False
        st.session_state["status"] = "Parado"
        st.session_state["loop_stop_flag"] = True
        st.info("🛑 Loop parado!")
        st.rerun()

with col3:
    if st.button("🔄 Limpar Histórico"):
        st.session_state["message_history"] = {}
        st.session_state["loop_count"] = 0
        st.session_state["net_logs"] = []
        st.success("🗑️ Histórico limpo!")
        st.rerun()

# Configurações
with st.expander("⚙️ Configurações", expanded=False):
    col_cfg1, col_cfg2 = st.columns(2)
    
    with col_cfg1:
        st.session_state["webhook_url"] = st.text_input(
            "URL do Webhook",
            value=st.session_state.get("webhook_url", WEBHOOK_MAIN_URL)
        )
    
    with col_cfg2:
        mode = st.selectbox(
            "Modo de números:",
            ["real_leads", "random", "sequential"],
            index=["real_leads", "random", "sequential"].index(
                st.session_state.get("number_generation_mode", "real_leads")
            )
        )
        if mode != st.session_state.get("number_generation_mode"):
            st.session_state["number_generation_mode"] = mode
            st.session_state["current_number_index"] = 0

    # Teste manual
    st.markdown("**🧪 Teste Manual:**")
    col_test1, col_test2 = st.columns(2)
    
    with col_test1:
        if st.button("🔥 Teste Rápido", type="primary"):
            test_number = get_next_dynamic_number()
            test_payload = {"timestamp": time.time(), "numero": test_number, "test": True}
            
            try:
                with st.spinner("Testando conexão..."):
                    response = call_webhook(st.session_state["webhook_url"], test_payload)
                
                if response.status_code == 200:
                    st.success(f"✅ **WEBHOOK FUNCIONANDO!** Número: {test_number}")
                    st.balloons()
                else:
                    st.error(f"❌ Erro {response.status_code}: {response.text[:100]}")
                    st.warning("🔧 Verifique se o workflow está ativo no n8n!")
            except Exception as e:
                st.error(f"❌ Falha na conexão: {e}")
                st.warning("🔧 Verifique se o n8n está online!")
    
    with col_test2:
        if st.button("🔍 Ver Próximo Número"):
            next_num = get_next_dynamic_number()
            st.code(f"Próximo: {next_num}")
            
            # Verificar se já foi enviado
            if is_message_already_sent(next_num):
                st.warning("⚠️ Este número já recebeu mensagem")
            else:
                st.success("✅ Número disponível para envio")

# Logs recentes e debug
if st.session_state.get("net_logs"):
    with st.expander("📋 Debug - Últimas Operações", expanded=True):
        st.caption("🔍 Acompanhe em tempo real o que está sendo enviado para o n8n:")
        
        # Mostrar últimos 8 logs
        recent_logs = st.session_state["net_logs"][-8:]
        for log in recent_logs:
            if log.get("action") == "SENDING":
                st.info(f"📤 {log['when']} - Enviando ciclo {log.get('cycle', '?')} - Número: **{log.get('numero', 'N/A')}**")
            elif log.get("action") == "SUCCESS":
                st.success(f"✅ {log['when']} - Sucesso! Número {log.get('numero', 'N/A')} - Status {log.get('status', '?')}")
            elif log.get("action") == "ERROR":
                st.error(f"❌ {log['when']} - Erro {log.get('status', '?')} - Número {log.get('numero', 'N/A')}")
                if log.get("error"):
                    st.caption(f"Detalhes: {log['error']}")
            elif log.get("action") == "EXCEPTION":
                st.error(f"🚨 {log['when']} - Exceção: {log.get('error', 'Erro desconhecido')}")
            elif log.get("action") == "POST":
                st.write(f"🔗 {log['when']} - HTTP {log.get('status', '?')} - Número: {log.get('payload', {}).get('numero', 'N/A')}")
        
        # Estatísticas rápidas
        if len(recent_logs) > 0:
            success_count = len([l for l in recent_logs if l.get("action") == "SUCCESS"])
            error_count = len([l for l in recent_logs if l.get("action") == "ERROR"])
            st.caption(f"📊 Últimas operações: {success_count} sucessos, {error_count} erros")

# Lógica do loop - execução automática
if st.session_state.get("loop_active", False):
    current_time = time.time()
    last_execution = st.session_state.get("last_loop_execution", 0)
    loop_delay = st.session_state.get("loop_delay", 10)
    
    if current_time - last_execution >= loop_delay:
        # Executar ciclo
        continue_loop = execute_single_loop_cycle()
        st.session_state["last_loop_execution"] = current_time
        
        if not continue_loop:
            st.session_state["loop_active"] = False
            st.session_state["status"] = "Parado"
    
    # Auto-refresh para manter o loop
    time.sleep(1)
    st.rerun()