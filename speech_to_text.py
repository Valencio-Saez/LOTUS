import os
import speech_recognition as sr
import keyboard  # To detect spacebar press
from pydub import AudioSegment

def prepare_voice_file(path: str) -> str:
    if os.path.splitext(path)[1] == '.wav':
        return path
    elif os.path.splitext(path)[1] in ('.mp3', '.m4a', '.ogg', '.flac'):
        audio_file = AudioSegment.from_file(path, format=os.path.splitext(path)[1][1:])
        wav_file = os.path.splitext(path)[0] + '.wav'
        audio_file.export(wav_file, format='wav')
        return wav_file
    else:
        raise ValueError(f'Unsupported audio format: {os.path.splitext(path)[1]}')

def transcribe_audio(audio_data, language="en-US") -> str:
    r = sr.Recognizer()
    try:
        text = r.recognize_google(audio_data, language=language)
        return text
    except sr.UnknownValueError:
        return "[Unrecognized Speech]"
    except sr.RequestError:
        return "[Speech Recognition Service Unavailable]"

def write_transcription_to_file(text, output_file) -> None:
    with open(output_file, 'a') as f:
        f.write(text + '\n')

def speech_to_text(input_path: str, output_path: str, language="en-US") -> None:
    wav_file = prepare_voice_file(input_path)
    with sr.AudioFile(wav_file) as source:
        audio_data = sr.Recognizer().record(source)
        text = transcribe_audio(audio_data, language)
        write_transcription_to_file(text, output_path)
        print('Transcription:')
        print(text)

def continuous_speech_to_text(language="en-US", output_file="live_output.txt") -> None:
    r = sr.Recognizer()
    print("LOTUS: SPEECH TO TEXT APPLICATION")
    print("\nPress spacebar to start recording.")
    
    while not keyboard.is_pressed('space'):
        pass  # Wait for the user to press spacebar to start
    
    print("Recording started... Speak now! Press spacebar again to stop.")
    
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        try:
            while True:
                if keyboard.is_pressed('space'):
                    print("Recording stopped.")
                    break
                audio_data = r.listen(source, timeout=10, phrase_time_limit=5)
                text = transcribe_audio(audio_data, language)
                print("Transcription:", text)
                write_transcription_to_file(text, output_file)
        except sr.WaitTimeoutError:
            pass

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu():
    while True:
        clear_screen()
        print("\nSelect an option:")
        print("1. Convert Audio File to Text")
        print("2. Convert Live Recording to Text")
        
        choice = input("Enter your choice (1 or 2): ").strip()
        
        if choice == "1":
            print("Please enter the path to an audio file (WAV, MP3, M4A, OGG, or FLAC):")
            input_path = input().strip()
            if not os.path.isfile(input_path):
                print("Error: File not found.")
            else:
                print("Please enter the path to the output file:")
                output_path = input().strip()
                try:
                    speech_to_text(input_path, output_path)
                except Exception as e:
                    print("Error:", e)
        elif choice == "2":
            print("Starting live recording... Press spacebar to start and stop.")
            continuous_speech_to_text()
        else:
            print("Invalid choice. Please enter 1 or 2.")

if __name__ == '__main__':
    main_menu()
