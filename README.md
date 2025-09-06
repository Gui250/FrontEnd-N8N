<p align="center">
  <img src="https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png" alt="Streamlit" height="64" />
</p>

## Envio Leads Dashboard (Streamlit + n8n)

Aplicação em Streamlit para controlar um fluxo no n8n e visualizar análise de dados em uma página separada (Dashboard).

### Funcionalidades

- Iniciar e parar o fluxo principal no n8n
- Exibir e acionar a URL de espera (webhook) do nó Wait quando disponível
- Página `Dashboard` com upload de arquivo (CSV/XLSX) e gráfico (sem exibir a tabela)
- Layout responsivo com estilos e (opcionalmente) animações Lottie

---

### Requisitos

- Python 3.9+
- Pip

### Instalação

```bash
cd /Users/guilhermemoreno/Desktop/dashboard_envioleads
python -m venv .venv
source .venv/bin/activate    # macOS/Linux
# .venv\Scripts\activate     # Windows PowerShell
pip install -r requirements.txt
```

### Executando

```bash
streamlit run main.py
```

O menu lateral mostrará a página `Dashboard` separada.

---

### Configuração do n8n (importante)

- Em `main.py`, ajuste a constante `WEBHOOK_MAIN_URL` para o endpoint do seu Webhook no n8n (mesmo ambiente, ex.: somente `/webhook` ou somente `/webhook-test`).
- Configure o Node Webhook do n8n para responder imediatamente (Response → Respond, Response Mode → On Received) nos endpoints de iniciar/parar, evitando timeout no cliente.
- Caso use nó `Wait → Wait for Webhook`, a URL de retomada é gerada em tempo de execução (`{{$resumeWebhookUrl}}`). Exponha-a para o app de uma destas formas:
  - Callback: um Node HTTP Request envia `resumeUrl` para seu backend/app quando o Wait é alcançado
  - Endpoint de status: um fluxo secundário no n8n devolve a `resumeUrl` quando consultado

Observação: o código trata automaticamente 404 com mensagem “Did you mean to make a GET request?” tentando GET quando o Webhook do n8n está configurado para esse método.

---

### Estrutura do Projeto

```
dashboard_envioleads/
├─ main.py                # Controle do fluxo n8n (iniciar/parar, wait URL)
├─ requirements.txt       # Dependências
└─ pages/
   └─ Dashboard.py        # Página de análise (upload + gráfico)
```

---

### Dicas e Solução de Problemas

- 404 indicando método incorreto: verifique se o Node Webhook no n8n usa o mesmo método enviado (POST/GET). O app tenta fallback para GET quando detecta a dica do n8n.
- Timeout ao iniciar/parar: habilite resposta imediata no Webhook (On Received) para não esperar o fluxo concluir.
- Animações Lottie: são opcionais. Instale com `pip install streamlit-lottie`. Se não estiver instalado, o app segue funcionando sem animações.

---

### Licença

Este projeto é de uso interno. Adapte conforme sua necessidade.
