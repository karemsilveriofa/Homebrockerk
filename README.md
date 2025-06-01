# Bot Sinais para IQ Option / Exnova

## Como usar

1. Coloque os ativos no arquivo `ativos.txt`, um ativo por linha (ex: CAD/CHF.OFX).
2. Defina o status do bot em `status.txt` como `on` para ativar ou `off` para desativar.
3. Configure os tokens em `conf.py` ou configure variáveis de ambiente para deploy.
4. Instale as dependências:

```
pip install -r requirements.txt
```

5. Rode o bot:

```
python3 main.py
```

O bot enviará sinais 10 segundos antes do início da próxima vela de 1 minuto.

## Deploy na Render

1. Crie um repositório no GitHub com estes arquivos.
2. No Render, crie um novo Web Service conectado ao seu repo.
3. Configure branch, runtime python 3, build command e start command:

- Build Command: `pip install -r requirements.txt`
- Start Command: `python3 main.py`

4. Configure as variáveis de ambiente (Settings > Environment):

- `TELEGRAM_TOKEN`
- `TELEGRAM_CHAT_ID`
- `API_KEY`
- `PORT=10000`

5. Faça deploy e o bot começará a enviar sinais.

## Controle

- Altere o arquivo `status.txt` para `on` ou `off` para ligar ou desligar o bot.
- Modifique os ativos em `ativos.txt` para adicionar ou remover ativos.
