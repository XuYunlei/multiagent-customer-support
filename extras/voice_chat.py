# extras/voice_chat.py
import sys
from pathlib import Path
import asyncio
import tempfile
import wave

import numpy as np
import sounddevice as sd
import simpleaudio as sa
from openai import OpenAI

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

agents_dir = project_root / "agents"
if str(agents_dir) not in sys.path:
    sys.path.insert(0, str(agents_dir))

from agents.router_agent import RouterAgent


client = OpenAI()  # uses OPENAI_API_KEY


def record_audio(duration: float = 5.0, samplerate: int = 16000) -> Path:
    """
    Record audio from the default microphone for `duration` seconds,
    save it as a temporary WAV file, and return its path.
    """
    print(f"\n🎙 Recording for {duration} seconds... Speak now!")
    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,                     # mono
        dtype="int16",
    )
    sd.wait()
    print("✅ Recording complete.\n")

    temp_wav = Path(tempfile.mktemp(suffix=".wav"))
    with wave.open(str(temp_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(samplerate)
        wf.writeframes(audio.tobytes())

    return temp_wav


def play_audio(audio_path: Path):
    """
    Play MP3 or WAV audio using pydub.
    """
    print("🔊 Playing audio response...")
    audio = AudioSegment.from_file(str(audio_path))
    play(audio)


def transcribe_audio(wav_path: Path) -> str:
    """
    Use OpenAI's Whisper model to transcribe speech to text.
    """
    print("🧠 Transcribing audio with OpenAI Whisper...")
    with open(wav_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
        )
    text = transcript.text.strip()
    print(f"📝 Transcribed text: {text!r}\n")
    return text


from pydub import AudioSegment
from pydub.playback import play

def synthesize_speech(text: str) -> Path:
    """
    Convert text to MP3 speech using OpenAI TTS.
    """
    print("🗣 Generating spoken response with OpenAI TTS...")

    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )

    out_path = Path(tempfile.mktemp(suffix=".mp3"))

    # Save MP3 bytes
    with open(out_path, "wb") as f:
        f.write(response.read())

    print(f"🔊 Audio response saved to {out_path}\n")
    return out_path


async def voice_loop():
    router = RouterAgent()

    print("\n===================================")
    print("   VOICE MULTI-AGENT ASSISTANT 🎧")
    print("===================================")
    print("Say something about your account, billing, or support.")
    print("Type 'exit' and press Enter to quit.\n")

    while True:
        cmd = input("Press Enter to record 5 seconds, or type 'exit' to quit: ").strip()
        if cmd.lower() == "exit":
            print("Goodbye! 👋")
            break

        # 1) Record from mic
        wav_in = record_audio(duration=5.0)

        # 2) Transcribe speech → text
        user_text = transcribe_audio(wav_in)
        if not user_text:
            print("No speech detected. Try again.\n")
            continue

        # 3) Run through RouterAgent (multi-agent pipeline)
        print("[Router] Processing your request via multi-agent system...\n")
        reply_text = await router.execute(user_text, customer_id=1)

        print("\n--- TEXT RESPONSE ---")
        print(reply_text)
        print("---------------------\n")

        # 4) TTS: Convert reply text → audio
        wav_out = synthesize_speech(reply_text)

        # 5) Play audio reply
        play_audio(wav_out)


if __name__ == "__main__":
    asyncio.run(voice_loop())
