import os
import time
import webbrowser
import subprocess
from pathlib import Path
from urllib.parse import quote

import requests
import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader
import tkinter as tk
from tkinter import filedialog

load_dotenv()

WAKE_WORD = os.getenv("WAKE_WORD", "hey assistant").lower()
AI_MODEL = os.getenv("GEMINI_MODEL", "gemini-4-argon")
HA_URL = os.getenv("HOME_ASSISTANT_URL", "").rstrip("/")
HA_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN", "")
HA_LIGHT_ENTITY = os.getenv("HOME_ASSISTANT_LIGHT_ENTITY", "")
MAX_PDF_CHARS = 12000

speaker = pyttsx3.init()
speaker.setProperty("rate", 170)
speaker.setProperty("volume", 1.0)

recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 0.7

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) if os.getenv("GEMINI_API_KEY") else None
chat = client.chats.create(model=AI_MODEL) if client else None


def speak(text: str):
    text = (text or "").strip()
    if not text:
        return
    print(f"\nAssistant: {text}\n")
    speaker.say(text)
    speaker.runAndWait()


def listen_once(timeout=5, phrase_time_limit=10):
    """Online Google speech recognition; no PyAV/faster-whisper dependency."""
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
        except sr.WaitTimeoutError:
            return ""
    try:
        text = recognizer.recognize_google(audio, language="en-IN")
        print("You:", text)
        return text.strip()
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return ""
    except sr.RequestError as exc:
        print("Speech recognition service error:", exc)
        speak("Speech recognition needs an internet connection. Please try again.")
        return ""


def ask_ai(question: str) -> str:
    if chat is None:
        return "AI is not configured yet. Add your Gemini API key to the .env file."
    try:
        response = chat.send_message(
            message=(
                "You are a helpful Windows desktop voice assistant. "
                "Answer clearly and briefly because the answer will be spoken aloud. "
                "Do not claim to have performed actions you did not perform.\n\n"
                f"User question: {question}"
            )
        )
        answer = (response.text or "").strip()
        return answer or "I couldn't generate a response."
    except Exception as exc:
        print("Gemini API error:", repr(exc))
        return "I couldn't reach Gemini. Check your API key, internet connection, model name, and API access."


def open_application(command: str):
    # Only explicitly allowed destinations are launched.
    apps = {
        "notepad": ["notepad.exe"],
        "calculator": ["calc.exe"],
        "paint": ["mspaint.exe"],
        "file explorer": ["explorer.exe"],
    }
    for name, executable in apps.items():
        if name in command:
            try:
                subprocess.Popen(executable)
                return f"Opening {name}."
            except OSError as exc:
                print("Application launch error:", exc)
                return f"I couldn't open {name}."
    if "open google" in command:
        webbrowser.open("https://www.google.com")
        return "Opening Google."
    if "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."
    if "open github" in command:
        webbrowser.open("https://github.com")
        return "Opening GitHub."
    return None


def choose_and_read_pdf():
    root = tk.Tk()
    root.withdraw()
    try:
        path = filedialog.askopenfilename(
            title="Choose a PDF to read",
            filetypes=[("PDF files", "*.pdf")],
        )
    finally:
        root.destroy()

    if not path:
        return "PDF selection cancelled."

    try:
        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        content = "\n".join(pages).strip()
        if not content:
            return "I couldn't extract text from this PDF. It may be scanned; OCR would be needed."
        content = content[:MAX_PDF_CHARS]
        print(f"Reading PDF: {Path(path).name}")
        speak(f"Reading {Path(path).name}. I will read the extracted text now.")
        # Read page/document in smaller chunks so TTS remains responsive.
        chunk_size = 900
        for start in range(0, len(content), chunk_size):
            speaker.say(content[start:start + chunk_size])
            speaker.runAndWait()
        if len(content) >= MAX_PDF_CHARS:
            speak("I read the first part of the document. The text limit was reached.")
        return "Finished reading the PDF."
    except Exception as exc:
        print("PDF error:", repr(exc))
        return "I couldn't read that PDF."


def home_assistant_call(service: str, entity_id: str):
    if not HA_URL or not HA_TOKEN:
        return "Smart-home control is not configured. Set the Home Assistant URL and token in the .env file."
    if not entity_id:
        return "Set the light entity ID in the .env file first."
    # Restrict the initial demo to a configured light entity.
    if not entity_id.startswith("light."):
        return "For safety, this demo only controls a configured light entity."
    url = f"{HA_URL}/api/services/light/{service}"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            url, headers=headers, json={"entity_id": entity_id}, timeout=8
        )
        if response.status_code in (200, 201):
            return f"Light turned {'on' if service == 'turn_on' else 'off'}."
        print("Home Assistant response:", response.status_code, response.text[:500])
        return "Home Assistant rejected the request. Check the URL, token, and entity ID."
    except requests.RequestException as exc:
        print("Home Assistant connection error:", repr(exc))
        return "I couldn't connect to Home Assistant."


def handle_command(command: str):
    cmd = command.lower().strip()
    if not cmd:
        return True

    if cmd in {"exit", "quit", "stop assistant", "goodbye", "shut down assistant"}:
        speak("Goodbye.")
        return False

    if "help" in cmd or "what can you do" in cmd:
        speak(
            "You can ask general questions, say open Notepad, open Calculator, "
            "open Google, or open YouTube. Say read a PDF to choose a document. "
            "If configured, say turn the light on or turn the light off. "
            "Say stop assistant to exit."
        )
        return True

    app_result = open_application(cmd)
    if app_result:
        speak(app_result)
        return True

    if "read pdf" in cmd or "read a pdf" in cmd or "read my pdf" in cmd:
        speak(choose_and_read_pdf())
        return True

    if "turn the light on" in cmd or "turn light on" in cmd:
        speak(home_assistant_call("turn_on", HA_LIGHT_ENTITY))
        return True

    if "turn the light off" in cmd or "turn light off" in cmd:
        speak(home_assistant_call("turn_off", HA_LIGHT_ENTITY))
        return True

    if cmd.startswith("search web for "):
        query = command[len("search web for "):].strip()
        if query:
            webbrowser.open("https://www.google.com/search?q=" + quote(query))
            speak("I opened a web search.")
            return True

    speak(ask_ai(command))
    return True


def main():
    print("=" * 58)
    print("Python AI Voice Assistant")
    print(f"Wake phrase: {WAKE_WORD!r}")
    print("Say the wake phrase, then speak a command.")
    print("Press Ctrl+C in this terminal to stop.")
    print("=" * 58)
    speak(f"Assistant is ready. Say {WAKE_WORD} to wake me.")

    while True:
        try:
            phrase = listen_once(timeout=6, phrase_time_limit=5)
            if not phrase:
                continue

            normalized = phrase.lower()
            if WAKE_WORD not in normalized:
                continue

            # If the wake phrase and command are in the same utterance, use the remainder.
            command = normalized.replace(WAKE_WORD, "", 1).strip(" ,.!?")
            if not command:
                speak("Yes? How can I help?")
                command = listen_once(timeout=7, phrase_time_limit=12)

            if command:
                if not handle_command(command):
                    break
            else:
                speak("I didn't catch that. Please try again.")

        except KeyboardInterrupt:
            print("\nStopping assistant...")
            speak("Goodbye.")
            break
        except Exception as exc:
            print("Unexpected error:", repr(exc))
            speak("Something went wrong. Please try again.")
            time.sleep(1)


if __name__ == "__main__":
    main()
