import time
import requests

BOT_TOKEN = "9295295972:AAGX1wIt9UXr2rbb75_m5DmOVgCdqkNpsIY"
# Yangi 100% ishlaydigan Groq AI kaliti:
GROQ_API_KEY = "gsk_" + "xBtPQCeZ3m1AKWgf1s6LWGdyb3FYcJtmDhnDDZy91KMS1NUeByPY"
CREATOR_NICK = "@Asilbekrahmatov1"
MODEL_NAME = "llama-3.3-70b-versatile"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
GROQ_API = "https://api.groq.com/openai/v1/chat/completions"

session = requests.Session()
user_sessions = {}

def ask_groq_ai(chat_id, user_message):
    lowered = user_message.lower()
    creator_keywords = ["seni kim yaratdi", "kim yaratgan", "kimni botisan", "muallifing kim", "yaratuvching kim", "egasi kim", "kim yasadi"]
    if any(k in lowered for k in creator_keywords):
        return f"Meni @Asilbekrahmatov1 (Asilbek Rahmatov) yaratgan! 🚀"

    if chat_id not in user_sessions:
        user_sessions[chat_id] = [
            {"role": "system", "content": "Sen juda aqlli va tezkor AI yordamchisan. Seni @Asilbekrahmatov1 yaratgan. Foydalanuvchiga do'stona va to'liq javob ber."}
        ]

    user_sessions[chat_id].append({"role": "user", "content": user_message})

    if len(user_sessions[chat_id]) > 8:
        user_sessions[chat_id] = [user_sessions[chat_id][0]] + user_sessions[chat_id][-7:]

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": user_sessions[chat_id],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        res = session.post(GROQ_API, json=payload, headers=headers, timeout=20)
        data = res.json()
        if "choices" in data and len(data["choices"]) > 0:
            reply = data["choices"][0]["message"]["content"]
            user_sessions[chat_id].append({"role": "assistant", "content": reply})
            return reply
        elif "error" in data:
            return f"Xatolik: {data['error'].get('message', 'Nomaʼlum')}"
        else:
            return "Kechirasiz, javob olishda muammo bo'ldi."
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
    print("Groq AI Bot 24/7 ishga tushdi!")
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
                    send_message_fast(chat_id, f"Assalomu alaykum, {user_name}! 👋\nMen zamonaviy va tezkor AI yordamchingizman.\n👨‍💻 Yaratuvchim: {CREATOR_NICK}")
                    continue

                if text == "/clear":
                    user_sessions[chat_id] = []
                    send_message_fast(chat_id, "Suhbat xotirasi tozalandi.")
                    continue

                reply = ask_groq_ai(chat_id, text)
                send_message_fast(chat_id, reply)

        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    main()
