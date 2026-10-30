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
session.headers.update({"User-Agent": "Mozilla/5.0"})
user_sessions = {}

def ask_groq_ai(chat_id, user_message, is_voice=False):
    """Matnli va ovozli savollarga to'g'ridan-to'g'ri AI javobi"""
    lowered = user_message.lower()
    creator_keywords = ["seni kim yaratdi", "kim yaratgan", "kimni botisan", "muallifing kim", "yaratuvching kim", "egasi kim", "kim yasadi"]
    if any(k in lowered for k in creator_keywords):
        return f"Meni @Asilbekrahmatov1 (Asilbek Rahmatov) yaratgan! 🚀"

    if chat_id not in user_sessions:
        user_sessions[chat_id] = [
            {"role": "system", "content": "Sen aqlli, quvnoq va har tomonlama yordam beruvchi do'stona AI yordamchisan. Seni @Asilbekrahmatov1 yaratgan. Foydalanuvchi bilan o'zbek tilida tabiiy suhbatlash. Foydalanuvchi ovozli xabar yuborsa, ovoz matniga to'g'ridan-to'g'ri to'liq javob qaytar (ovozni eshita olmasliging haqida aslo gapirma)."}
        ]

    prompt_content = user_message
    if is_voice:
        prompt_content = f"[Foydalanuvchi ovozi matni]: {user_message}. Ushbu savolga darhol to'liq va aniq javob ber."

    user_sessions[chat_id].append({"role": "user", "content": prompt_content})

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
        res = session.post(GROQ_CHAT_API, json=payload, headers=headers, timeout=25)
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

def transcribe_audio_groq(file_url):
    """Ovozli xabarni (Voice) matnga aylantirish (Whisper)"""
    try:
        audio_data = session.get(file_url, timeout=25).content
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        files = {
            "file": ("voice.oga", audio_data, "audio/ogg"),
            "model": (None, "whisper-large-v3")
        }
        res = session.post(GROQ_AUDIO_API, headers=headers, files=files, timeout=30)
        result = res.json()
        return result.get("text", "").strip()
    except Exception as e:
        print(f"Audio xatosi: {e}")
        return ""

def send_generated_image(chat_id, prompt):
    """Rasm chizish (Pollinations AI)"""
    send_message_fast(chat_id, f"🎨 Rasm chizilmoqda: \"{prompt}\"...\nBiroz kuting.")
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
        res = session.post(url, data=data, timeout=35)
        if res.status_code != 200:
            send_message_fast(chat_id, f"Rasm tayyor! Uni ko'rish: {image_url}")
    except Exception as e:
        send_message_fast(chat_id, f"Rasm chizishda xatolik: {e}")

def send_message_fast(chat_id, text):
    try:
        if len(text) > 4000:
            for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
                session.post(f"{TELEGRAM_API}/sendMessage", data={"chat_id": chat_id, "text": chunk}, timeout=6)
        else:
            session.post(f"{TELEGRAM_API}/sendMessage", data={"chat_id": chat_id, "text": text}, timeout=6)
    except Exception:
        pass

def main():
    print("🚀 Barcha funksiyalari to'liq AI Bot ishga tushdi!")
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
                    send_message_fast(chat_id, "🎙 Ovoz eshitilmoqda...")
                    
                    file_info = session.get(f"{TELEGRAM_API}/getFile?file_id={file_id}").json()
                    file_path = file_info.get("result", {}).get("file_path")

                    if file_path:
                        voice_url = f"{TELEGRAM_FILE_API}/{file_path}"
                        user_text = transcribe_audio_groq(voice_url)
                        if user_text:
                            send_message_fast(chat_id, f"🗣 Siz aytdingiz: \"{user_text}\"")
                            reply = ask_groq_ai(chat_id, user_text, is_voice=True)
                            send_message_fast(chat_id, reply)
                        else:
                            send_message_fast(chat_id, "Ovozingizni aniqlay olmadim. Qaytadan gapirib ko'ring.")
                    continue

                text = msg.get("text", "")
                if not text:
                    continue

                # /start buyrug'i
                if text == "/start":
                    welcome = (
                        f"Assalomu alaykum, {user_name}! 👋\n\n"
                        f"Men barcha imkoniyatlarga ega aqlli AI yordamchingizman:\n\n"
                        f"💬 <b>Matn:</b> Menga istalgan savolni yozing.\n"
                        f"🎙 <b>Ovoz:</b> Ovozli xabar yuborsangiz, to'liq tushunib javob beraman.\n"
                        f"🎨 <b>Rasm chizish:</b> <code>/rasm tavsif</code> deb yozing.\n\n"
                        f"👨‍💻 Yaratuvchim: {CREATOR_NICK}"
                    )
                    session.post(f"{TELEGRAM_API}/sendMessage", data={"chat_id": chat_id, "text": welcome, "parse_mode": "HTML"})
                    continue

                if text == "/clear":
                    user_sessions[chat_id] = []
                    send_message_fast(chat_id, "Suhbat xotirasi tozalandi.")
                    continue

                # 2. RASM CHIZISH
                if text.startswith("/rasm") or text.startswith("/image") or text.lower().startswith("rasm chiz"):
                    prompt = text.replace("/rasm", "").replace("/image", "").replace("rasm chiz", "").strip()
                    if prompt:
                        send_generated_image(chat_id, prompt)
                    else:
                        send_message_fast(chat_id, "Iltimos, rasm tavsifini yozing. Masalan: /rasm moviy ko'l va tog'lar")
                    continue

                # 3. ODDIY MATN
                reply = ask_groq_ai(chat_id, text)
                send_message_fast(chat_id, reply)

        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    main()
