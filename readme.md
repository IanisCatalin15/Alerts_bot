# CRM Alerts Bot

Bot Python care verifica periodic ticketele din CRM si trimite alerte pe Telegram.

## Ce face
- citeste tickete din CRM (Playwright)
- aplica reguli de alertare (`checker.py`)
- trimite notificari pe Telegram (`notifier.py`)
- evita duplicatele folosind `state.db`

## Fisiere
- `main.py` - job scheduler + flow principal
- `scraper.py` - login CRM + extragere tickete
- `checker.py` - reguli de alerta
- `notifier.py` - trimitere mesaje Telegram (chat + forum topics)
- `state.py` - persistenta locala SQLite
- `config.py` - variabile `.env`

## Setup rapid
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## `.env` minim
```env
CRM_URL=https://.../it-core
CRM_URL_GROUP3=https://.../it-departament
CRM_URL_RETAIL_WAREHOUSE=https://.../retail-warehouse
CRM_LOGIN_URL=https://.../auth
CRM_USERNAME=user
CRM_PASSWORD=pass

TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_DESTINATIONS=-1001234567890,-1001234567890:12

CHECK_INTERVAL_MINUTES=5
ALERT_THRESHOLD_MINUTES=30
```

`TELEGRAM_DESTINATIONS`:
- `chat_id` => mesaj in chat principal
- `chat_id:thread_id` => mesaj in topic (Telegram Forum)

## Run
```bash
python3 main.py
```
