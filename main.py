import os
import time
import requests
import urllib.parse

# ================= SOZLAMALAR =================
BOT_TOKEN = "9295295972:AAGX1wIt9UXr2rbb75_m5DmOVgCdqkNpsIY"
GROQ_API_KEY = "gsk_" + "xBtPQCeZ3m1AKWgf1s6LWGdyb3FYcJtmDhnDDZy91KMS1NUeByPY"
CREATOR_NICK = "@Asilbekrahmatov1"
MODEL_NAME = "openai/gpt-oss-120b"
# ===============================================

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
TELEGRAM_FILE_API = f"https://api.telegram.org/file/bot{BOT_TOKEN}"
GROQ_CHAT_API = "https://api.groq.com/openai/v1/chat/completions"
GROQ_AUDIO_API = "https://api.groq.com/openai/v1/audio/transcriptions"

session = requests.Session()
user_sessions = {}

def ask_groq_ai(chat_id, user_message):
    """Matnli savollarga aqlli AI javobi"""
    lowered = user_message.lower()
    creator_keywords = ["seni kim yaratdi", "kim yaratgan", "kimni botisan", "muallifing kim", "yaratuvching kim", "egasi kim", "kim yasadi"]
    if any(k in lowered for k in creator_keywords):
        return f"Meni @Asilbekrahmatov1 (Asilbek Rahmatov) yaratgan! 🚀"

    if chat_id not in user_sessions:
        user_sessions[chat_id] = [
            {"role": "system", "content": "Sen juda aqlli va tezkor AI yordamchisan. Seni @Asilbekrahmatov1 yaratgan. Foydalanuvchiga do'stona, to'liq va o'zbek tilida chiroyli javob ber."}
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
        res = session.post(GROQ_CHAT_API, json=payload, headers=headers, timeout=20)
        data = res.json()
        if "choices" in data and len(data["choices"]) > 0:
            reply = data["choices"][0]["message"]["content"]
            user_sessions[chat_id].append({"role": "assistant", "content": reply})
            return reply
        elif "error" in data:
            return f"Xatolik: {data['error'].get('message', 'Nomaʼlum')}"
        else:
            return "Kechirasiz, javob shakllanmadi."
    except Exception as e:
        return f"Ulanish xatosi: {e}"

def transcribe_audio_groq(file_url):
    """2-FUNKSIYA: Ovozli xabarni matnga aylantirish (Whisper)"""
    try:
        audio_data = session.get(file_url, timeout=20).content
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        files = {
            "file": ("voice.oga", audio_data, "audio/ogg"),
            "model": (None, "whisper-large-v3")
        }
        res = session.post(GROQ_AUDIO_API, headers=headers, files=files, timeout=30)
        result = res.json()
        return result.get("text", "")
    except Exception as e:
        print(f"Audio xatosi: {e}")
        return ""

def send_generated_image(chat_id, prompt):
    """3-FUNKSIYA: Rasm chizish (AI Image)"""
    send_message_fast(chat_id, f"🎨 Rasm chizilmoqda: \"{prompt}\"...\nIltimos, bir necha soniya kuting.")
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        
        url = f"{TELEGRAM_API}/sendPhoto"
        data = {
            "chat_id": chat_id,
            "photo": image_url,
            "caption": f"🖼 <b>{prompt}</b>\n\n👨‍💻 Yaratuvchi: {CREATOR_NICK}",
            "parse_mode": "HTML"
        }
        res = session.post(url, data=data, timeout=30)
        if res.status_code != 200:
            send_message_fast(chat_id, f"Rasm tayyor! Uni ko'rish: {image_url}")
    except Exception as e:
        send_message_fast(chat_id, f"Rasm chizishda xatolik bo'ldi: {e}")

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
    print("🚀 Yangilangan Multimodal AI Bot 24/7 ishga tushdi!")
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
                user_name = msg["chat"].get("first_name", "Foydalanuvchi")

                # 1. OVOZLI XABARLARNI QABUL QILISH
                if "voice" in msg or "audio" in msg:
                    file_id = msg["voice"]["file_id"] if "voice" in msg else msg["audio"]["file_id"]
                    send_message_fast(chat_id, "🎙 Ovozli xabaringiz eshitilmoqda...")
                    
                    file_info = session.get(f"{TELEGRAM_API}/getFile?file_id={file_id}").json()
                    file_path = file_info.get("result", {}).get("file_path")

                    if file_path:
                        voice_url = f"{TELEGRAM_FILE_API}/{file_path}"
                        user_text = transcribe_audio_groq(voice_url)
                        if user_text:
                            send_message_fast(chat_id, f"🗣 Siz aytdingiz: \"{user_text}\"")
                            reply = ask_groq_ai(chat_id, user_text)
                            send_message_fast(chat_id, reply)
                        else:
                            send_message_fast(chat_id, "Ovozni aniqlab bo'lmadi. Qaytadan aniqroq gapiring.")
                    continue

                text = msg.get("text", "")
                if not text:
                    continue

                if text == "/start":
                    welcome = (
                        f"Assalomu alaykum, {user_name}! 👋\n\n"
                        f"Men koʻp funksiyali aqlli AI yordamchingizman:\n\n"
                        f"💬 <b>Matn:</b> Menga istalgan savolingizni bering.\n"
                        f"🎙 <b>Ovoz:</b> Ovozli xabar yuborsangiz, eshitib javob beraman.\n"
                        f"🎨 <b>Rasm chizish:</b> /rasm deb yozing (masalan: <code>/rasm kosmosdagi mashina</code>)\n\n"
                        f"👨‍💻 Yaratuvchim: {CREATOR_NICK}"
                    )
                    session.post(f"{TELEGRAM_API}/sendMessage", data={"chat_id": chat_id, "text": welcome, "parse_mode": "HTML"})
                    continue

                if text == "/clear":
                    user_sessions[chat_id] = []
                    send_message_fast(chat_id, "Suhbat xotirasi tozalandi.")
                    continue

                # 2. RASM CHIZISH BUYRUG'I
                if text.startswith("/rasm") or text.startswith("/image"):
                    prompt = text.replace("/rasm", "").replace("/image", "").strip()
                    if prompt:
                        send_generated_image(chat_id, prompt)
                    else:
                        send_message_fast(chat_id, "Iltimos, rasm tavsifini yozing. Masalan: /rasm Samarqand kechasi")
                    continue

                # 3. ODDIY MATNLI SUHBAT
                reply = ask_groq_ai(chat_id, text)
                send_message_fast(chat_id, reply)

        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    main()
