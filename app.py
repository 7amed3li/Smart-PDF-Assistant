import google.generativeai as genai
import PyPDF2
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import os
import json
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
            "ar": "Yanıtınız tamamen Arapça olmalıdır.",
            "tr": "Yanıtınız tamamen Türkçe olmalıdır.",
            "en": "Your response must be entirely in English."
        }.get(lang, "Yanıtınız tamamen Türkçe olmalıdır.")

        full_prompt = f"{lang_instruction}\n\n📄 PDF İçeriği:\n{pdf_content}\n\n❓ Soru: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ Gemini API hatası: {e}"

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
            return "⚠️ Ses tanıma servisi hatası", "tr"

# Metni sese dönüştür
def text_to_speech(text, lang, chat_id):
    filename = os.path.join(AUDIO_FOLDER, f"{chat_id}_yanit_{len(st.session_state.chat_history[chat_id]) + 1}.mp3")
    lang_dict = {"Türkçe": "tr", "Arapça": "ar", "İngilizce": "en"}
    chosen_lang = lang_dict[lang]

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
    
    # Sohbet geçmişini yükle
    chat_history = load_chat_history()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = chat_history
    
    # PDF yükleme
    if "pdf_content" not in st.session_state:
        st.session_state.pdf_content = None

    uploaded_file = st.sidebar.file_uploader("📂 PDF Dosyanızı Yükleyin", type="pdf")
    if uploaded_file and st.session_state.pdf_content is None:
        with st.spinner("🔄 Dosya yükleniyor..."):
            st.session_state.pdf_content = read_pdf(uploaded_file)
            if st.session_state.pdf_content:
                st.sidebar.success("✅ PDF başarıyla yüklendi!")
            else:
                st.sidebar.warning("⚠️ Dosya içeriği boş veya okunamadı.")

    # Sohbet geçmişini gösteren yan panel
    st.sidebar.title("💬 Geçmiş Sohbetler")
    chat_ids = list(st.session_state.chat_history.keys())
    selected_chat = st.sidebar.radio("Bir sohbet seçin:", chat_ids, index=0 if chat_ids else None)

    if st.sidebar.button("➕ Yeni Sohbet"):
        new_chat_id = f"Sohbet {len(chat_ids) + 1}"
        st.session_state.chat_history[new_chat_id] = []
        save_chat_history(st.session_state.chat_history)
        selected_chat = new_chat_id

    if st.sidebar.button("🗑️ Bu Sohbeti Sil"):
        if selected_chat in st.session_state.chat_history:
            del st.session_state.chat_history[selected_chat]
            save_chat_history(st.session_state.chat_history)
            selected_chat = None

    if selected_chat:
        st.title(f"💬 {selected_chat}")

        # Sohbeti göster
        for entry in st.session_state.chat_history[selected_chat]:
            st.markdown(f"🧑‍💻 **Siz:** {entry['question']}")
            st.markdown(f"🤖 **Bot:** {entry['answer']}")
            if "audio" in entry and entry["audio"]:
                st.audio(entry["audio"])
            st.markdown("---")

        user_input = st.text_input("💬 Sorunuzu yazın:", key="user_input")
        selected_language = st.selectbox("🎙️ Sesli kayıt dili:", ["Türkçe", "Arapça", "İngilizce"])

        if st.button("📩 Gönder"):
            if user_input:
                st.info("⏳ Soru analiz ediliyor ve yanıt oluşturuluyor...")
                lang = detect_language(user_input)
                response = get_response_from_gemini(user_input, st.session_state.pdf_content, lang)
                st.success("✅ Yanıt alındı!")
                st.session_state.chat_history[selected_chat].append({"question": user_input, "answer": response})
                save_chat_history(st.session_state.chat_history)

        if st.button("🎤 Ses Kaydı"):
            question, lang = record_audio(selected_language)
            response = get_response_from_gemini(question, st.session_state.pdf_content, lang)
            audio_file = text_to_speech(response, lang, selected_chat)
            st.session_state.chat_history[selected_chat].append({"question": question, "answer": response, "audio": audio_file})
            save_chat_history(st.session_state.chat_history)

if __name__ == "__main__":
    main()
