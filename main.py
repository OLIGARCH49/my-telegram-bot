import os
import time
import requests
import urllib.parse
import re
import json

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

def translate_to_english_prompt(text):
    """O'zbekcha so'zni rasmlar uchun toza inglizcha promptga aylantirish"""
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are a translator for image generation. Translate user input into a short descriptive English prompt (3-6 words) for photo generation. ONLY return the English words, nothing else."},
                {"role": "user", "content": text}
            ],
            "temperature": 0.1,
            "max_tokens": 30
        }
        res = session.post(GROQ_CHAT_API, json=payload, headers=headers, timeout=10)
        en_prompt = res.json()["choices"][0]["message"]["content"].strip().replace('"', '').replace('.', '')
        return en_prompt
    except Exception:
        return text

def ask_groq_ai(chat_id, user_message, is_voice=False):
    """Matnli va ovozli savollarga to'g'ri AI javobi"""
    lowered = user_message.lower()
    creator_keywords = ["seni kim yaratdi", "kim yaratgan", "kimni botisan", "muallifing kim", "yaratuvching kim", "egasi kim", "kim yasadi"]
    if any(k in lowered for k in creator_keywords):
        return f"Meni @Asilbekrahmatov1 (Asilbek Rahmatov) yaratgan! 🚀"

    if chat_id not in user_sessions:
        user_sessions[chat_id] = [
            {"role": "system", "content": "Sen juda aqlli va do'stona AI yordamchisan. Seni @Asilbekrahmatov1 yaratgan. Foydalanuvchi bilan o'zbek tilida tabiiy suhbatlash. DIQQAT: Hech qachon ASCII chiziqli matnli rasmlar chizma, bunday qilish taqiqlanadi! Agar foydalanuvchi rasm so'rasa, /rasm buyrug'idan foydalanishni ayt."}
        ]

    prompt_content = user_message
    if is_voice:
        prompt_content = f"[Foydalanuvchi ovozli xabar yo'lladi]: {user_message}. Ushbu savolga o'zbek tilida to'liq va lo'nda javob ber."

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
            reply = re.sub(r'```[\s\S]*?```', '', reply).strip()
            user_sessions[chat_id].append({"role": "assistant", "content": reply})
            return reply if reply else "Savolingizga javob tayyor!"
        elif "error" in data:
            return f"Xatolik: {data['error'].get('message', 'Nomaʼlum')}"
        else:
            return "Kechirasiz, javob olishda muammo bo'ldi."
    except Exception as e:
        return f"Ulanish xatosi: {e}"

def transcribe_audio_groq(file_url):
    """Ovozli xabarni matnga aylantirish"""
    try:
        audio_data = session.get(file_url, timeout=25).content
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        files = {
            "file": ("voice.oga", audio_data, "audio/ogg"),
            "model": (None, "whisper-large-v3")
        }
        res = session.post(GROQ_AUDIO_API, headers=headers, files=files, timeout=30)
        return res.json().get("text", "").strip()
    except Exception:
        return ""

def send_generated_image(chat_id, original_prompt):
    """Haqiqiy 100% foto-rasm chizish (Pollinations AI)"""
    send_message_fast(chat_id, f"🎨 Rasm chizilmoqda: \"{original_prompt}\"...\nBiroz kuting.")
    try:
        en_prompt = translate_to_english_prompt(original_prompt)
        clean_prompt = f"{en_prompt} realistic detailed photography 4k"
        encoded = urllib.parse.quote(clean_prompt)
        seed = int(time.time())
        image_url = f"https://image.pollinations.ai/prompt/{encoded}?seed={seed}&nologo=true"

        url = f"{TELEGRAM_API}/sendPhoto"
        data = {
            "chat_id": chat_id,
            "photo": image_url,
            "caption": f"🖼 <b>{original_prompt}</b>\n\n👨‍💻 Yaratuvchi: {CREATOR_NICK}",
            "parse_mode": "HTML"
        }
        res = session.post(url, data=data, timeout=40)
        if res.status_code != 200:
            send_message_fast(chat_id, f"Rasm tayyor! Havola orqali ko'ring: {image_url}")
    except Exception as e:
        send_message_fast(chat_id, f"Rasm chizishda xatolik: {e}")

def get_main_keyboard():
    """Doimiy pastki tugmalar menyusi"""
    return json.dumps({
        "keyboard": [
            [{"text": "🎨 Rasm chizish"}, {"text": "🎙 Ovozli xabar"}],
            [{"text": "ℹ️ Yordam / Buyruqlar"}, {"text": "🧹 Xotirani tozalash"}],
            [{"text": "👨‍💻 Yaratuvchi"}]
        ],
        "resize_keyboard": True
    })

def send_message_fast(chat_id, text, reply_markup=None):
    try:
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            data["reply_markup"] = reply_markup
        session.post(f"{TELEGRAM_API}/sendMessage", data=data, timeout=8)
    except Exception:
        pass

def main():
    print("🚀 Mukammal AI Bot 24/7 ishga tushdi!")
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

                # 1. OVOZLI XABARLAR
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
                            send_message_fast(chat_id, reply, get_main_keyboard())
                    continue

                text = msg.get("text", "")
                if not text:
                    continue

                # /start buyrug'i
                if text == "/start":
                    welcome = (
                        f"Assalomu alaykum, {user_name}! 👋\n\n"
                        f"Men barcha imkoniyatlarga ega aqlli AI yordamchingizman!\n\n"
                        f"Pastdagi <b>Menyu tugmalari</b> orqali botdan oson foydalanishingiz mumkin 👇\n\n"
                        f"👨‍💻 Yaratuvchim: {CREATOR_NICK}"
                    )
                    send_message_fast(chat_id, welcome, get_main_keyboard())
                    continue

                # Tugmalar va buyruqlar
                if text == "ℹ️ Yordam / Buyruqlar" or text == "/help":
                    help_text = (
                        f"📖 <b>BOT BUYRUQLARI VA QO'LLANMA:</b>\n\n"
                        f"🎨 <b>Rasm chizish:</b>\n"
                        f"Buyruq: <code>/rasm kelajakdagi shahar</code> yoki <code>/rasm kompyuter</code>\n"
                        f"<i>(Istalgan narsani yozsangiz, bot haqiqiy foto qilib beradi)</i>\n\n"
                        f"🎙 <b>Ovozli xabar:</b>\n"
                        f"Menga mikrofon orqali ovozli xabar yuborsangiz, eshitib javob qaytaraman.\n\n"
                        f"💬 <b>Oddiy savollar:</b>\n"
                        f"Istalgan dars, matematika yoki qiziqtirgan mavzuda savol bering.\n\n"
                        f"🧹 <b>Xotirani tozalash:</b> /clear\n"
                        f"👨‍💻 <b>Yaratuvchi:</b> /creator"
                    )
                    send_message_fast(chat_id, help_text, get_main_keyboard())
                    continue

                if text == "🎨 Rasm chizish":
                    send_message_fast(chat_id, "🎨 Rasm chizish uchun quyidagicha yozing:\n\n<code>/rasm kompyuter va stol</code>\nyoki\n<code>/rasm kelajakdagi shahar</code>", get_main_keyboard())
                    continue

                if text == "🎙 Ovozli xabar":
                    send_message_fast(chat_id, "🎙 Menga mikrofonni bosib xohlagan savolingizni ovozli xabar qilib yuboring, eshitib javob beraman!", get_main_keyboard())
                    continue

                if text == "🧹 Xotirani tozalash" or text == "/clear":
                    user_sessions[chat_id] = []
                    send_message_fast(chat_id, "🧹 Suhbat xotirasi tozalandi. Yangi savolingizni bering!", get_main_keyboard())
                    continue

                if text == "👨‍💻 Yaratuvchi" or text == "/creator":
                    send_message_fast(chat_id, f"Meni @Asilbekrahmatov1 (Asilbek Rahmatov) yaratgan! 🚀", get_main_keyboard())
                    continue

                # Rasm chizish
                lowered_text = text.lower()
                if lowered_text.startswith("/rasm") or lowered_text.startswith("/image") or "rasmini chiz" in lowered_text or "rasm chiz" in lowered_text:
                    prompt = text.replace("/rasm", "").replace("/image", "").replace("rasmini chiz", "").replace("rasm chiz", "").strip()
                    if prompt:
                        send_generated_image(chat_id, prompt)
                    else:
                        send_message_fast(chat_id, "Iltimos, rasm tavsifini yozing. Masalan: /rasm kompyuter")
                    continue

                # Oddiy savol
                reply = ask_groq_ai(chat_id, text)
                send_message_fast(chat_id, reply, get_main_keyboard())

        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    main()
