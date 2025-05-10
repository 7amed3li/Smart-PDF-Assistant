import google.generativeai as genai
import PyPDF2
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
import json
import time
from typing import Optional
from langdetect import detect

# Gemini API Anahtarı
API_KEY = "AIzaSyD3k9GoAKRSSAWG2_pcwxy3g5_1aC8Zy30"
genai.configure(api_key=API_KEY)

# Sohbet geçmişini ve ses dosyalarını saklama yolları
CHAT_HISTORY_FILE = "sohbet_gecmisi.json"
AUDIO_FOLDER = "sesli_yanitlar"

# Sesli yanıtlar için klasör oluştur
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

# Sohbet geçmişini yükle
def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}

# Sohbet geçmişini kaydet
def save_chat_history(history):
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, ensure_ascii=False, indent=4)

# PDF dosyasını oku
def read_pdf(file) -> Optional[str]:
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted.strip() + "\n"
        return text if text else None
    except Exception as e:
        st.error(f"⚠️ PDF okunurken hata oluştu: {e}")
        return None

# Dili algıla
def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        return lang if lang in ["ar", "en", "tr"] else "tr"
    except:
        return "tr"

# Gemini ile yanıt oluştur
def get_response_from_gemini(prompt: str, pdf_content: str, lang: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        lang_instruction = {
            "ar": "الرد بالعربية فقط.",
            "tr": "Yanıtınız tamamen Türkçe olmalıdır.",
            "en": "Your response must be entirely in English."
        }.get(lang, "Yanıtınız tamamen Türkçe olmalıdır.")

        full_prompt = f"{lang_instruction}\n\n📄 PDF İçeriği:\n{pdf_content}\n\n❓ Soru: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Gemini API hatası: {e}"

# تلخيص محتوى PDF
def summarize_pdf(pdf_content: str, lang: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        lang_instruction = {
            "ar": "قم بتلخيص النص التالي باللغة العربية في حدود 150-200 كلمة.",
            "tr": "Aşağıdaki metni Türkçe olarak 150-200 kelime arasında özetleyin.",
            "en": "Summarize the following text in English within 150-200 words."
        }.get(lang, "Aşağıdaki metni Türkçe olarak 150-200 kelime arasında özetleyin.")

        max_length = 5000
        if len(pdf_content) > max_length:
            pdf_content = pdf_content[:max_length] + "\n... (Kısaltıldı)"

        full_prompt = f"{lang_instruction}\n\n📄 PDF İçeriği:\n{pdf_content}"
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ خطأ أثناء تلخيص الملف: {e}"

# Ses kaydı al
def record_audio(selected_lang):
    recognizer = sr.Recognizer()
    lang_dict = {"Türkçe": "tr-TR", "Arapça": "ar-SA", "İngilizce": "en-US"}
    chosen_language = lang_dict[selected_lang]

    with sr.Microphone() as source:
        st.info(f"🎤 Konuşun ({selected_lang})...")
        audio = recognizer.listen(source, timeout=7)

        try:
            detected_text = recognizer.recognize_google(audio, language=chosen_language)
            st.success(f"✅ Algılanan ses: {detected_text}")
            return detected_text, selected_lang
        except sr.UnknownValueError:
            return "❌ Ses anlaşılamadı", "tr"
        except sr.RequestError:
            return "⚠️ Ses tanıما servisi hatası", "tr"

# Metni sese dönüştür
def text_to_speech(text, lang, chat_id):
    timestamp = int(time.time())
    filename = os.path.join(AUDIO_FOLDER, f"{chat_id}_yanit_{timestamp}.mp3")
    lang_dict = {
        "tr": "tr", "Türkçe": "tr",
        "ar": "ar", "Arapça": "ar",
        "en": "en", "İngilizce": "en"
    }
    chosen_lang = lang_dict.get(lang, "tr")

    try:
        tts = gTTS(text=text, lang=chosen_lang)
        tts.save(filename)
        return filename
    except Exception as e:
        st.error(f"⚠️ Ses dosyası oluşturulurken hata oluştu: {e}")
        return None

# Streamlit Arayüzü
def main():
    st.set_page_config(page_title="📖 PDF Sohbet Botu", layout="wide")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = load_chat_history()
    if "pdf_content" not in st.session_state:
        st.session_state.pdf_content = None
    if "last_response" not in st.session_state:
        st.session_state.last_response = None
    if "awaiting_response" not in st.session_state:
        st.session_state.awaiting_response = False
    if "awaiting_audio_response" not in st.session_state:
        st.session_state.awaiting_audio_response = False
    if "selected_chat" not in st.session_state:
        st.session_state.selected_chat = None

    # إدارة تحميل PDF
    st.sidebar.title("📂 PDF Yükleme")
    uploaded_file = st.sidebar.file_uploader("PDF Dosyanızı Yükleyin", type="pdf", key="pdf_uploader")
    if uploaded_file:
        with st.spinner("🔄 Dosya yükleniyor..."):
            st.session_state.pdf_content = read_pdf(uploaded_file)
            st.session_state.last_response = None  # إعادة تعيين الاستجابة
            if st.session_state.pdf_content:
                st.sidebar.success("✅ PDF başarıyla yüklendi!")
            else:
                st.sidebar.warning("⚠️ Dosya içeriği boş veya okunامadı.")

    if st.session_state.pdf_content and st.sidebar.button("🗑️ PDF'yi Sil", key="clear_pdf"):
        st.session_state.pdf_content = None
        st.session_state.last_response = None
        st.sidebar.success("✅ PDF kaldırıldı!")

    st.sidebar.title("💬 Geçmiş Sohbetler")
    chat_ids = list(st.session_state.chat_history.keys())
    if not chat_ids:
        st.sidebar.info("Henüz sohbet yok. Yeni bir sohbet başlatın!")
        selected_chat = None
    else:
        selected_chat = st.sidebar.radio("Bir sohbet seçin:", chat_ids, index=0, key="chat_selector")
        if selected_chat != st.session_state.selected_chat:
            st.session_state.selected_chat = selected_chat
            st.session_state.last_response = None  # إعادة تعيين الاستجابة عند تغيير المحادثة
            st.rerun()

    if st.sidebar.button("➕ Yeni Sohbet", key="new_chat"):
        new_chat_id = f"Sohbet {len(chat_ids) + 1}"
        st.session_state.chat_history[new_chat_id] = []
        save_chat_history(st.session_state.chat_history)
        st.session_state.selected_chat = new_chat_id
        st.session_state.last_response = None
        st.rerun()

    if st.sidebar.button("🗑️ Bu Sohbeti Sil", key="delete_chat") and selected_chat:
        del st.session_state.chat_history[selected_chat]
        save_chat_history(st.session_state.chat_history)
        st.session_state.selected_chat = None
        st.session_state.last_response = None
        st.rerun()

    if selected_chat:
        st.title(f"💬 {selected_chat}")

        for entry in st.session_state.chat_history[selected_chat]:
            st.markdown(f"🧑‍💻 **Siz:** {entry['question']}")
            st.markdown(f"🤖 **Bot:** {entry['answer']}")
            if "audio" in entry and entry["audio"]:
                st.audio(entry["audio"])
            st.markdown("---")

        # زر تلخيص PDF
        if st.session_state.pdf_content:
            if st.button("📝 PDF Özeti", key="summarize_pdf"):
                with st.spinner("🔄 Dosya özetleniyor..."):
                    lang = detect_language(st.session_state.pdf_content)
                    summary = summarize_pdf(st.session_state.pdf_content, lang)
                    st.success(f"✅ Özet oluşturuldu ({lang})!")
                    st.markdown(f"📄 **Özet:**\n{summary}")
                    st.session_state.chat_history[selected_chat].append({
                        "question": "PDF özeti isteği",
                        "answer": summary
                    })
                    save_chat_history(st.session_state.chat_history)
                    st.session_state.last_response = None

        user_input = st.text_input("💬 Sorunuzu yazın:", key=f"user_input_{selected_chat}", value="")
        selected_language = st.selectbox("🎙️ Sesli kayıt dili:", ["Türkçe", "Arapça", "İngilizce"], key=f"lang_select_{selected_chat}")

        if st.button("📩 Gönder", key=f"send_text_{selected_chat}") and user_input and not st.session_state.awaiting_response:
            if not st.session_state.pdf_content:
                st.warning("⚠️ Lütfen önce bir PDF dosyası yükleyin!")
            else:
                st.session_state.awaiting_response = True
                lang = detect_language(user_input)
                response = get_response_from_gemini(user_input, st.session_state.pdf_content, lang)
                st.session_state.last_response = response
                st.session_state.chat_history[selected_chat].append({"question": user_input, "answer": response})
                save_chat_history(st.session_state.chat_history)
                st.session_state.awaiting_response = False

        if st.session_state.last_response:
            st.success("✅ Yanıt alındı!")
            st.markdown(f"🤖 **Bot:** {st.session_state.last_response}")

        if st.button("🎤 Ses Kaydı", key=f"record_audio_{selected_chat}") and not st.session_state.awaiting_audio_response:
            if not st.session_state.pdf_content:
                st.warning("⚠️ Lütfen önce bir PDF dosyası yükleyin!")
            else:
                st.session_state.awaiting_audio_response = True
                question, spoken_lang = record_audio(selected_language)
                lang = detect_language(question)
                if question.startswith("❌") or question.startswith("⚠️"):
                    st.warning(question)
                    st.session_state.awaiting_audio_response = False
                else:
                    response = get_response_from_gemini(question, st.session_state.pdf_content, lang)
                    audio_file = text_to_speech(response, lang, selected_chat)
                    st.session_state.chat_history[selected_chat].append({
                        "question": question,
                        "answer": response,
                        "audio": audio_file
                    })
                    save_chat_history(st.session_state.chat_history)
                    st.success("✅ Sesli yanıt oluşturuldu!")
                    if audio_file:
                        st.audio(audio_file)
                    st.session_state.awaiting_audio_response = False

if __name__ == "__main__":
    main()
