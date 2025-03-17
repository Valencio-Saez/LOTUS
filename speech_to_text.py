import os
import speech_recognition as sr
import keyboard  # To detect spacebar press
from pydub import AudioSegment

def prepare_voice_file(path: str) -> str:
    """
    Converts the input audio file to WAV format if necessary and returns the path to the WAV file.
    """
    if os.path.splitext(path)[1] == '.wav':
        return path
    elif os.path.splitext(path)[1] in ('.mp3', '.m4a', '.ogg', '.flac'):
        audio_file = AudioSegment.from_file(path, format=os.path.splitext(path)[1][1:])
        wav_file = os.path.splitext(path)[0] + '.wav'
        audio_file.export(wav_file, format='wav')
        return wav_file
    else:
        raise ValueError(f'Unsupported audio format: {os.path.splitext(path)[1]}')

def transcribe_audio(audio_data, language) -> str:
    """
    Transcribes audio data to text using Google's speech recognition API.
    """
    r = sr.Recognizer()
    try:
        text = r.recognize_google(audio_data, language=language)
        return text
    except sr.UnknownValueError:
        return "[Unrecognized Speech]"
    except sr.RequestError:
        return "[Speech Recognition Service Unavailable]"

def write_transcription_to_file(text, output_file) -> None:
    """
    Appends the transcribed text to the output file.
    """
    with open(output_file, 'a') as f:
        f.write(text + '\n')

def continuous_speech_to_text(language: str = "en-US", output_file: str = "output.txt") -> None:
    """
    Continuously records speech and transcribes it every few seconds.
    Stops when the spacebar is pressed again.
    """
    r = sr.Recognizer()
    recording = False
    with sr.Microphone() as source:
        print("LOTUS: SPEECH TO TEXT APPLICATION")
        print("Ambient noise detected. Adjustments complete. Ready to record!")
        print("\nPress spacebar to start recording. Press it again to stop.")

        r.adjust_for_ambient_noise(source)  # Adjusting for ambient noise
        
        while True:
            if keyboard.is_pressed('space'):
                if not recording:
                    print("Recording started... Speak now!")
                    recording = True
                else:
                    print("Recording stopped.")
                    break
            
            try:
                audio_data = r.listen(source, timeout=10, phrase_time_limit=5)  # Capture short clips
                text = transcribe_audio(audio_data, language)
                print("Transcription:", text)
                write_transcription_to_file(text, output_file)  # Append transcription
            except sr.WaitTimeoutError:
                continue  # No speech detected, continue listening

if __name__ == '__main__':
    continuous_speech_to_text()
