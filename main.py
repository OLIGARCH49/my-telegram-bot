import time
import requests

BOT_TOKEN = "9295295972:AAGX1wIt9UXr2rbb75_m5DmOVgCdqkNpsIY"
GEMINI_API_KEY = "AQ.Ab8RN6JgImQpixS9Glfm7EVQDbY8DQOQCN7txgnk1-pr1YZawQ"
ACTIVE_MODEL = "models/gemini-2.5-flash"
CREATOR_NICK = "@Asilbekrahmatov1"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
session = requests.Session()
user_sessions = {}

def ask_gemini_fast(chat_id, user_message):
    lowered = user_message.lower()
    creator_keywords = ["seni kim yaratdi", "kim yaratgan", "kimni botisan", "muallifing kim", "yaratuvching kim", "egasi kim", "kim yasadi"]
    if any(k in lowered for k in creator_keywords):
        return f"Meni @Asilbekrahmatov1 (Asilbek Rahmatov) yaratgan! 🚀"

    if chat_id not in user_sessions:
        user_sessions[chat_id] = []
    user_sessions[chat_id].append({"role": "user", "parts": [{"text": user_message}]})
    if len(user_sessions[chat_id]) > 6:
        user_sessions[chat_id] = user_sessions[chat_id][-6:]

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/{ACTIVE_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": user_sessions[chat_id],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 800}
    }
    try:
        res = session.post(endpoint, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
        data = res.json()
        if "candidates" in data and len(data["candidates"]) > 0:
            reply = data["candidates"][0]["content"]["parts"][0]["text"]
            user_sessions[chat_id].append({"role": "model", "parts": [{"text": reply}]})
            return reply
        elif "error" in data:
            return f"⚠️ Gemini xatosi: {data['error'].get('message', 'Nomaʼlum')}"
        else:
            return f"Kechirasiz, serverdan javob kelmadi: {str(data)[:150]}"
    except Exception as e:
        return f"Ulanish xatosi: {e}"

def send_message_fast(chat_id, text):
    try:
        if len(text) > 4000:
            for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
                session.post(f"{TELEGRAM_API}/sendMessage", data={"chat_id": chat_id, "text": chunk}, timeout=5)
        else:
            session.post(f"{TELEGRAM_API}/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=5)
    except Exception:
        pass

def main():
    print("🤖 Telegram Bot 24/7 ishga tushdi!")
    last_update_id = 0
    while True:
        try:
            res = session.get(f"{TELEGRAM_API}/getUpdates", params={"offset": last_update_id + 1, "timeout": 10}, timeout=15)
            data = res.json()
            if not data.get("ok"):
                continue
            for update in data.get("result", []):
                last_update_id = update["update_id"]
                if "message" not in update:
                    continue
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                user_name = msg["chat"].get("first_name", "Foydalanuvchi")
                if not text:
                    continue
                if text == "/start":
                    send_message_fast(chat_id, f"Assalomu alaykum, {user_name}! 👋\nMen aqlli Gemini AI botiman.\n👨‍💻 Yaratuvchim: {CREATOR_NICK}")
                    continue
                if text == "/clear":
                    user_sessions[chat_id] = []
                    send_message_fast(chat_id, "🧹 Suhbat xotirasi tozalandi.")
                    continue
                reply = ask_gemini_fast(chat_id, text)
                send_message_fast(chat_id, reply)
        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    main()
