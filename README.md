# Python AI Voice Assistant (Windows) — Gemini API edition

Features:
- Wake phrase: "Hey Assistant"
- English (India) speech recognition through SpeechRecognition's Google recognizer
- AI general questions through Google's Gemini API (`google-genai`)
- Spoken replies with offline Windows text-to-speech via `pyttsx3`
- Opens a small allowlist of Windows applications and websites
- Opens a file picker and reads extractable text from PDFs
- Optional Home Assistant light on/off control

## Important notes

- Speech recognition uses an online Google recognition service, so an internet connection is required and audio is sent to that service for transcription. This is separate from the Gemini API call.
- AI questions use your Gemini API key and may be subject to quotas or charges based on your Google AI account and model. Keep the key private.
- Text-to-speech is local.
- Smart-home control is disabled until configured. Start with one non-critical light; do not expose Home Assistant to the public internet.
- PDF reading extracts embedded text. Scanned/image-only PDFs need OCR, which is not included.
- This starter listens in short intervals, so it is not a low-power always-on wake-word engine.

## 1. Requirements

Use 64-bit Python 3.11 on Windows for the easiest package compatibility. Python 3.13 may work for some packages, but audio dependencies can be less predictable.

Install Python from https://www.python.org/downloads/ and enable "Add python.exe to PATH".

## 2. Create and activate environment

Open PowerShell in this project folder:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

If PowerShell blocks activation, use Command Prompt instead:

```bat
venv\Scripts\activate.bat
```

If `PyAudio` fails to install, first confirm you are using 64-bit Python 3.11, then run:
`python -m pip install --only-binary=:all: PyAudio`

## 3. Get a Gemini API key

1. Open [Google AI Studio](https://aistudio.google.com/) and sign in.
2. Create an API key for the Gemini API.
3. Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

4. Edit `.env` and set `GEMINI_API_KEY` to your key. The default model is configured with `GEMINI_MODEL`. If that model is unavailable to your account, choose a currently available text-generation model in Google AI Studio and update the value.
5. Do not share the key or commit `.env` to Git.

The app uses Google's official `google-genai` Python SDK and Gemini chat API. See the [official Gemini API guide](https://ai.google.dev/api/generate-content).

## 4. Run

```powershell
python main.py
```

Say "Hey Assistant, what is Python?" or say "Hey Assistant" and then give a command.

## 5. Supported voice commands

- "Hey Assistant, what is Python?"
- "Hey Assistant, open Notepad"
- "Hey Assistant, open Calculator"
- "Hey Assistant, open File Explorer"
- "Hey Assistant, open Google"
- "Hey Assistant, open YouTube"
- "Hey Assistant, read a PDF"
- "Hey Assistant, turn the light on"
- "Hey Assistant, turn the light off"
- "Hey Assistant, help"
- "Hey Assistant, stop assistant"

Only the explicitly listed applications are launched by voice. This avoids arbitrary shell commands.

## 6. Optional Home Assistant setup

1. Set up Home Assistant and add your light/device there first.
2. In Home Assistant, open your user profile and create a Long-Lived Access Token.
3. Set `HOME_ASSISTANT_URL`, `HOME_ASSISTANT_TOKEN`, and `HOME_ASSISTANT_LIGHT_ENTITY` in `.env`.
4. The entity ID typically looks like `light.living_room`; use the exact ID shown in Home Assistant.
5. Restart the Python assistant and test with a non-critical light.

Treat the token like a password. Do not put it in source control. This starter only sends turn-on/turn-off commands to the single configured `light.*` entity.

## 7. Troubleshooting

### Microphone not found
- Windows Settings → Privacy & security → Microphone: allow desktop apps.
- Windows Settings → System → Sound: select the correct input device.
- Run `python -m pip show SpeechRecognition PyAudio`.

### "No Default Input Device Available"
Check the Windows recording device and microphone permissions. You can list devices with:

```python
import speech_recognition as sr
print(sr.Microphone.list_microphone_names())
```

### Speech recognition service error
Check internet access, microphone permissions, and try speaking clearly. This demo uses online speech recognition and is not fully offline.

### Gemini not configured or API error
- Confirm `.env` exists beside `main.py`.
- Check that `GEMINI_API_KEY` is set correctly and you restarted the process after editing `.env`.
- Verify the model name is available to your account and that your account has API access/quota.
- Do not paste your API key into chat, screenshots, or source control.

### PDF has no text
Some PDFs are scans/images. They require OCR before the assistant can read them.

### Home Assistant error
Verify the local URL, token, entity ID, and that the PC can reach Home Assistant. Never share the token in screenshots or chat.

## Project files

- `main.py` — assistant logic
- `requirements.txt` — Python dependencies
- `.env.example` — configuration template
- `.gitignore` — prevents committing secrets and virtual environment
