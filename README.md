Smart PDF Assistant - README.md
📖 Smart PDF Assistant

Smart PDF Assistant is an AI-powered chatbot that can read and analyze PDF files, answer questions about their content, and even summarize them using Gemini AI.

Supports Turkish, Arabic, and English, with both voice input and text-to-speech output.

🚀 Features (Updated: 2025-05-10)

- 🔹 Read and extract text from PDF files
- 🔹 Multilingual support: Turkish 🇹🇷, Arabic 🇸🇦, English 🇬🇧
- 🔹 Speech recognition for asking questions via microphone
- 🔹 Text-to-speech answers using Google TTS (.mp3 playback)
- 🔹 Automatic language detection for accurate responses
- 🔹 Summarizes PDF contents in 150–200 words
- 🔹 Maintains a full chat history per session (sohbet_gecmisi.json)
- 🔹 Supports multiple chat sessions and previous chat selection
- 🔹 Option to delete or create new chats
- 🔹 Interactive and modern Streamlit UI
- 🔹 Optional audio response generation and playback
- 🔹 Automatic voice file saving per response (sesli_yanitlar/ folder)
- 🔹 PDF removal/reset option in sidebar

📦 Installation

To install all required packages, run:

pip install -r requirements.txt

Or install them manually:

pip install streamlit PyPDF2 SpeechRecognition gTTS langdetect google-generativeai pyaudio

🎯 How to Use?

1️⃣ Launch the Streamlit app  
2️⃣ Upload a PDF file via the left sidebar  
3️⃣ Ask your question using text or voice input  
4️⃣ Get an AI-generated answer based on the content  
5️⃣ Optionally, listen to the answer using audio playback  
6️⃣ View or manage previous conversations in the sidebar

💻 Run the App

cd your_project_directory  
streamlit run app.py

📁 Project Structure

.
├── app.py                     # Main Streamlit app  
├── sohbet_gecmisi.json       # Chat history file  
├── sesli_yanitlar/           # Folder for generated audio replies  
└── README.md                 # This file

🧠 Powered by

- Gemini 1.5 Flash: https://deepmind.google/technologies/gemini/
- Google Text-to-Speech (gTTS): https://pypi.org/project/gTTS/
- Streamlit: https://streamlit.io/
