
import time
import requests
import telegram
from datetime import datetime, timedelta
import pytz
import threading
import os
from flask import Flask

try:
    from conf import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, API_KEY
except ImportError:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))
    API_KEY = os.getenv("API_KEY")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de Sinais Ativo"

def ler_ativos():
    try:
        with open('ativos.txt', 'r') as f:
            ativos = [linha.strip() for linha in f if linha.strip()]
        print(f"[DEBUG] Ativos carregados: {ativos}")
        return ativos
    except Exception as e:
        print(f"[ERRO] ao ler ativos.txt: {e}")
        return []

def ler_status():
    try:
        with open('status.txt', 'r') as f:
            status = f.read().strip().lower()
        print(f"[DEBUG] Status atual: {status}")
        return status == 'on'
    except Exception as e:
        print(f"[ERRO] ao ler status.txt: {e}")
        return False

def enviar_telegram(bot, mensagem):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensagem, parse_mode=telegram.ParseMode.HTML)
        print(f"[INFO] Sinal enviado: {mensagem}")
    except Exception as e:
        print(f"[ERRO] ao enviar mensagem Telegram: {e}")

def calcula_sinal(velas):
    try:
        closes = [float(v['close']) for v in velas]
        if len(closes) < 20:
            return None

        ma5 = sum(closes[-5:]) / 5
        ma10 = sum(closes[-10:]) / 10
        print(f"[DEBUG] MA5: {ma5} | MA10: {ma10}")

        if ma5 > ma10:
            return "COMPRA"
        elif ma5 < ma10:
            return "VENDA"
        else:
            return None
    except Exception as e:
        print(f"[ERRO] ao calcular sinal: {e}")
        return None

def pegar_velas(ativo, API_KEY):
    url = f"https://api.twelvedata.com/time_series?symbol={ativo}&interval=1min&apikey={API_KEY}&outputsize=20"
    try:
        resposta = requests.get(url)
        dados = resposta.json()
        if "values" in dados:
            return list(reversed(dados["values"]))
        else:
            print(f"[AVISO] Dados insuficientes para {ativo}. Nenhum sinal gerado.")
            return []
    except Exception as e:
        print(f"[ERRO] Erro na API para {ativo}: {e}")
        return []

def horario_corretora():
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)

def esperar_proximo_sinal():
    agora = horario_corretora()
    proxima_vela = (agora.replace(second=0, microsecond=0) + timedelta(minutes=1))
    esperar_segundos = (proxima_vela - agora).total_seconds() - 10
    if esperar_segundos > 0:
        print(f"[DEBUG] Aguardando {esperar_segundos:.2f}s para próximo sinal...")
        time.sleep(esperar_segundos)

def monitorar_ativo(ativo, bot):
    print(f"[INFO] Iniciando monitoramento de {ativo}")

    while True:
        if not ler_status():
            print("[INFO] Bot está OFF")
            time.sleep(10)
            continue

        esperar_proximo_sinal()

        velas = pegar_velas(ativo, API_KEY)
        sinal = calcula_sinal(velas)
        agora = horario_corretora().strftime('%Y-%m-%d %H:%M:%S')

        if sinal:
            mensagem = (f"⏰ {agora}\n"
                        f"Ativo: <b>{ativo}</b>\n"
                        f"Sinal: <b>{sinal}</b>")
            enviar_telegram(bot, mensagem)
        else:
            print(f"[INFO] Nenhum sinal gerado para {ativo} às {agora}")

        time.sleep(60)

def iniciar_threads(bot, ativos):
    for ativo in ativos:
        t = threading.Thread(target=monitorar_ativo, args=(ativo, bot), daemon=True)
        t.start()
    print("[INFO] Monitoramento iniciado")

if __name__ == "__main__":
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    ativos = ler_ativos()
    if not ativos:
        print("[ERRO] Nenhum ativo encontrado em ativos.txt")
        exit(1)

    iniciar_threads(bot, ativos)
    port = int(os.environ.get("PORT", 10000))
    print(f"[INFO] Servidor Flask rodando na porta {port}")
    app.run(host='0.0.0.0', port=port)
