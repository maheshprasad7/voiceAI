"""Quick diagnostic script to test each component."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("AVAHAAN DIAGNOSTIC TOOL")
print("=" * 60)

# 1. Test .env loading
print("\n[1/5] Testing .env configuration...")
try:
    from config.settings import settings
    print(f"  ELEVENLABS_API_KEY: {'SET (' + settings.ELEVENLABS_API_KEY[:8] + '...)' if settings.ELEVENLABS_API_KEY else 'MISSING!'}")
    print(f"  GEMINI_API_KEY:     {'SET (' + settings.GEMINI_API_KEY[:8] + '...)' if settings.GEMINI_API_KEY else 'MISSING!'}")
    print(f"  VOICE_ID:           {settings.VOICE_ID}")
    print(f"  MODEL_NAME:         {settings.MODEL_NAME}")
    print(f"  WAKE_WORD:          {settings.WAKE_WORD}")
    print("  ✅ Config OK")
except Exception as e:
    print(f"  ❌ Config FAILED: {e}")
    sys.exit(1)

# 2. Test microphone
print("\n[2/5] Testing microphone (3 seconds)...")
try:
    import speech_recognition as sr
    r = sr.Recognizer()
    mic = sr.Microphone(device_index=settings.MIC_DEVICE_INDEX if settings.MIC_DEVICE_INDEX > 0 else None)
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1)
        print("  Speak something now...")
        audio = r.listen(source, timeout=3, phrase_time_limit=3)
    text = r.recognize_google(audio)
    print(f"  Heard: '{text}'")
    print("  ✅ Microphone + Google STT OK")
except sr.WaitTimeoutError:
    print("  ⚠️ No speech detected (silence) - mic might be OK, just quiet")
except sr.UnknownValueError:
    print("  ⚠️ Audio captured but couldn't understand - mic is working, speech unclear")
except Exception as e:
    print(f"  ❌ Microphone FAILED: {e}")

# 3. Test Gemini API
print("\n[3/5] Testing Gemini API...")
try:
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(model_name=settings.MODEL_NAME)
    response = model.generate_content("Say hello in one sentence.", stream=False)
    print(f"  Gemini says: '{response.text.strip()[:80]}'")
    print("  ✅ Gemini API OK")
except Exception as e:
    print(f"  ❌ Gemini API FAILED: {e}")

# 4. Test ElevenLabs TTS
print("\n[4/5] Testing ElevenLabs TTS...")
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
    client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
    
    def test_text():
        yield "Hello, I am working."
    
    audio_chunks = []
    stream = client.text_to_speech.convert_realtime(
        text=test_text(),
        voice_id=settings.VOICE_ID,
        model_id="eleven_turbo_v2_5",
        output_format="pcm_16000",
        voice_settings=VoiceSettings(stability=0.5, similarity_boost=0.8, style=0.0, use_speaker_boost=True)
    )
    for chunk in stream:
        if chunk:
            audio_chunks.append(chunk)
    
    total_bytes = sum(len(c) for c in audio_chunks)
    print(f"  Received {total_bytes} bytes of audio ({len(audio_chunks)} chunks)")
    
    if total_bytes > 0:
        # Try playing it
        import pyaudio
        pa = pyaudio.PyAudio()
        out_stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True)
        for c in audio_chunks:
            out_stream.write(c)
        out_stream.stop_stream()
        out_stream.close()
        pa.terminate()
        print("  ✅ ElevenLabs TTS OK - did you hear 'Hello, I am working'?")
    else:
        print("  ❌ ElevenLabs TTS returned 0 bytes")
except Exception as e:
    print(f"  ❌ ElevenLabs TTS FAILED: {e}")

# 5. Test Speaker
print("\n[5/5] Testing speaker output with a beep...")
try:
    import pyaudio
    import struct, math
    pa = pyaudio.PyAudio()
    out_stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, output=True)
    # Generate a 0.5s 440Hz beep
    for i in range(8000):
        sample = int(16000 * math.sin(2 * math.pi * 440 * i / 16000))
        out_stream.write(struct.pack('<h', sample))
    out_stream.stop_stream()
    out_stream.close()
    pa.terminate()
    print("  ✅ Speaker OK - did you hear a beep?")
except Exception as e:
    print(f"  ❌ Speaker FAILED: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
