import pvporcupine
import pyaudio
import struct
import os
from vosk import Model, KaldiRecognizer
import json
import RPi.GPIO as GPIO
import pyttsx3

# GPIO Setup
GPIO.setmode(GPIO.BCM)
LED_PIN = 17
GPIO.setup(LED_PIN, GPIO.OUT)

# Initialize Text-to-Speech
engine = pyttsx3.init()

# Porcupine Configuration (Wake Word)
porcupine = pvporcupine.create(
    access_key="YOUR_PORCUPINE_ACCESS_KEY",
    keyword_paths=["path/to/custom_wake_word.ppn"]
)

# Vosk Configuration (Speech Recognition)
model = Model("path/to/vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)

# Audio Configuration
pa = pyaudio.PyAudio()
audio_stream = pa.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length
)

def process_command(command):
    """Handle recognized voice commands"""
    print("Command:", command)
    if "turn on light" in command:
        GPIO.output(LED_PIN, GPIO.HIGH)
        speak("Turning on the light")
    elif "turn off light" in command:
        GPIO.output(LED_PIN, GPIO.LOW)
        speak("Turning off the light")
    elif "hello" in command:
        speak("Hello! How can I help you?")
    # Add more commands here

def speak(text):
    """Convert text to speech"""
    engine.say(text)
    engine.runAndWait()

def listen_for_command():
    """Listen and process voice command after wake word"""
    print("Listening for command...")
    frames = []
    for _ in range(0, int(16000 / 1024 * 3)):  # Listen for 3 seconds
        data = audio_stream.read(1024)
        frames.append(data)
    
    if recognizer.AcceptWaveform(b''.join(frames)):
        result = json.loads(recognizer.Result())
        return result['text']
    return None

try:
    print("System activated. Listening for wake word...")
    while True:
        pcm = audio_stream.read(porcupine.frame_length)
        pcm_unpacked = struct.unpack_from("h" * porcupine.frame_length, pcm)
        
        # Detect wake word
        keyword_index = porcupine.process(pcm_unpacked)
        
        if keyword_index >= 0:
            print("Wake word detected!")
            speak("Yes? I'm listening")
            command = listen_for_command()
            if command:
                process_command(command.lower())
            print("Returning to wake word detection")

except KeyboardInterrupt:
    print("Shutting down...")
finally:
    audio_stream.close()
    pa.terminate()
    porcupine.delete()
    GPIO.cleanup()