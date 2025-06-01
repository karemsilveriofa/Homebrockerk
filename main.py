import time
import requests
import telegram
from datetime import datetime, timedelta
import pytz
import threading
import os
from flask import Flask

# Importa configurações do arquivo conf.py ou variáveis ambiente
try:
    from conf import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, API_KEY
except ImportError:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))
    API_KEY = os.getenv("API_KEY")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ativo e rodando!"

# Função para ler ativos do arquivo ativos.txt
def ler_ativos():
    try:
        with open('ativos.txt', 'r') as f:
            ativos = [linha.strip() for linha in f if linha.strip()]
        return ativos
    except Exception as e:
        print(f"[ERRO] ao ler ativos.txt: {e}")
        return []

# Função para ler status on/off
def ler_status():
    try:
        with open('status.txt', 'r') as f:
            status = f.read().strip().lower()
        return status == 'on'
    except Exception as e:
        print(f"[ERRO] ao ler status.txt: {e}")
        return False

# Enviar mensagem para Telegram
def enviar_telegram(bot, mensagem):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem, parse_mode=telegram.ParseMode.HTML)
        print(f"[INFO] Sinal enviado: {mensagem}")
    except Exception as e:
        print(f"[ERRO] ao enviar mensagem Telegram: {e}")

# Estratégia simples: média móvel rápida x média móvel lenta para sinal
def calcula_sinal(velas):
    closes = [float(v['close']) for v in velas]
    if len(closes) < 20:
        return None  # Dados insuficientes

    ma_5 = sum(closes[-5:]) / 5
    ma_10 = sum(closes[-10:]) / 10

    if ma_5 > ma_10:
        return "COMPRA"
    elif ma_5 < ma_10:
        return "VENDA"
    else:
        return None

# Pega velas 1min do ativo da API Twelve Data
def pegar_velas(ativo, API_KEY):
    url = f'https://api.twelvedata.com/time_series?symbol={ativo}&interval=1min&outputsize=20&apikey={API_KEY}'
    try:
        resposta = requests.get(url, timeout=10)
        data = resposta.json()
        if 'values' in data:
            return list(reversed(data['values']))
        else:
            print(f"[ERRO] API retornou erro para {ativo}: {data.get('message', 'sem detalhes')}")
            return None
    except Exception as e:
        print(f"[ERRO] requisição API Twelve Data para {ativo}: {e}")
        return None

def horario_corretora():
    tz = pytz.timezone('America/Sao_Paulo')
    agora = datetime.now(tz)
    return agora

def esperar_proximo_sinal():
    agora = horario_corretora()
    proxima_vela = (agora.replace(second=0, microsecond=0) + timedelta(minutes=1))
    esperar_segundos = (proxima_vela - agora).total_seconds() - 10
    if esperar_segundos > 0:
        time.sleep(esperar_segundos)

def monitorar_ativo(ativo, bot):
    print(f"[INFO] Iniciando monitoramento do ativo {ativo}")

    ultimo_sinal = None

    while True:
        if not ler_status():
            print("[INFO] Bot está OFF. Aguardando para ativar...")
            time.sleep(10)
            continue

        esperar_proximo_sinal()

        velas = pegar_velas(ativo, API_KEY)
        if not velas:
            time.sleep(10)
            continue

        sinal = calcula_sinal(velas)
        agora = horario_corretora().strftime('%Y-%m-%d %H:%M:%S')

        if sinal and sinal != ultimo_sinal:
            mensagem = (f"⏰ {agora}\n"
                        f"Ativo: <b>{ativo}</b>\n"
                        f"Sinal: <b>{sinal}</b>\n"
                        f"Entrada prevista para próxima vela 1min.")
            enviar_telegram(bot, mensagem)
            ultimo_sinal = sinal
        else:
            print(f"[INFO] Sem mudança de sinal para {ativo}")

        time.sleep(1)

def iniciar_threads(bot, ativos):
    threads = []
    for ativo in ativos:
        t = threading.Thread(target=monitorar_ativo, args=(ativo, bot), daemon=True)
        threads.append(t)
        t.start()

    print("[INFO] Monitoramento iniciado para todos os ativos.")

if __name__ == "__main__":
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    ativos = ler_ativos()
    if not ativos:
        print("[ERRO] Nenhum ativo configurado no ativos.txt")
        exit(1)

    # Iniciar threads para monitorar ativos em background
    iniciar_threads(bot, ativos)

    # Rodar o servidor Flask para manter o Render feliz (não encerra o container)
    port = int(os.environ.get("PORT", 10000))
    print(f"[INFO] Servidor Flask rodando na porta {port}")
    app.run(host='0.0.0.0', port=port)
