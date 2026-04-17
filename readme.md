# 🤖 CRM Alerts Bot

Un bot de automatizare scris în Python care monitorizează ticketele dintr-un CRM și trimite alerte pe Telegram în timp real. Proiectul folosește scraping asincron și programare periodică pentru a detecta rapid problemele și a notifica echipa.

## 🚀 Ce face acest bot
- Verifică periodic ticket-ele din CRM
- Detectează ticket-ele care depășesc timpul limită de procesare
- Trimite alerte în Telegram pentru echipa de suport
- Stochează starea locală pentru a evita duplicatele

## 🛠️ Tehnologii
- **Python 3.10+**
- **Playwright** pentru scraping și navigare headless
- **APScheduler** pentru job-uri programate
- **python-telegram-bot** pentru trimiterea mesajelor în Telegram
- **SQLite** pentru stocare locală

## 📁 Structura proiectului
- `main.py` - Punctul de intrare al aplicației
- `scraper.py` - Extrage datele din CRM
- `checker.py` - Verifică regulile pentru alertare
- `notifier.py` - Trimite mesajele către Telegram
- `state.py` - Gestionează starea locală și `state.db`
- `config.py` - Încarcă variabilele din `.env`

## ⚙️ Instalare și configurare
1. Clonează proiectul și intră în director:
   ```bash
   cd ~/Desktop/Alerts_bot
   ```
2. Creează și activează mediul virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Instalează dependențele:
   ```bash
   pip install -r requirements.txt
   ```
4. Instalează browserul Playwright:
   ```bash
   playwright install chromium
   ```
5. Creează fișierul `.env` în directorul proiectului și adaugă variabilele necesare:
   ```env
   # URL-uri CRM
   CRM_URL="https://link-catre-tickete-it-core"
   CRM_URL_GROUP3="https://link-catre-tickete-departament"
   CRM_LOGIN_URL="https://link-login-crm"

   # Date de autentificare CRM
   CRM_USERNAME="nume.utilizator"
   CRM_PASSWORD="parola_ta_aici"

   # Date Telegram
   TELEGRAM_BOT_TOKEN="token_de_la_botfather"
   TELEGRAM_CHAT_ID="id_ul_grupului"

   # Setări opționale
   CHECK_INTERVAL_MINUTES=5
   ALERT_THRESHOLD_MINUTES=30
   ```

## ▶️ Pornire
După ce ai configurat mediul și `.env`, pornește aplicația:
```bash
python3 main.py
```

## 🧪 Observații
- În `requirements.txt` se află pachetele necesare pentru funcționare
- Dacă CRM-ul se schimbă, actualizează logica din `scraper.py`
- `state.db` se generează automat la prima rulare

## 💡 Recomandări
- Rulează bot-ul pe un server sau VM dedicat pentru a avea uptime constant
- Verifică periodic Telegram Bot API token și chat ID-ul
- Actualizează intervalul de verificare în funcție de volumul de ticketelor
