import os
import speech_recognition as sr
import keyboard
from pydub import AudioSegment

def convert_audio_to_wav(input_path: str) -> str:
    file_extension = os.path.splitext(input_path)[1].lower()
    if file_extension == '.wav':
        return input_path
    elif file_extension in ('.mp3', '.m4a', '.ogg', '.flac'):
        audio = AudioSegment.from_file(input_path, format=file_extension[1:])
        wav_path = os.path.splitext(input_path)[0] + '.wav'
        audio.export(wav_path, format='wav')
        return wav_path
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")

def get_transcription_from_audio(audio_data, lang="en-US") -> str:
    recognizer = sr.Recognizer()
    try:
        return recognizer.recognize_google(audio_data, language=lang)
    except sr.UnknownValueError:
        return "[Could not understand audio]"
    except sr.RequestError:
        return "[Service is unavailable]"

def append_transcription_to_file(transcription: str, output_path: str) -> None:
    with open(output_path, 'a') as file:
        file.write(transcription + '\n')

def transcribe_audio_file(input_path: str, output_path: str, lang="en-US") -> None:
    wav_file = convert_audio_to_wav(input_path)
    with sr.AudioFile(wav_file) as source:
        audio_data = sr.Recognizer().record(source)
        transcription = get_transcription_from_audio(audio_data, lang)
        append_transcription_to_file(transcription, output_path)
        print('Transcription complete:')
        print(transcription)

def record_live_audio_and_transcribe(lang="en-US", output_file="live_output.txt") -> None:
    recognizer = sr.Recognizer()
    print("Voice-to-Text Application")
    print("\nPress the spacebar to begin recording.")
    
    while not keyboard.is_pressed('space'):
        pass  # Wait for the spacebar to start recording
    
    print("Recording started... Speak now! Press spacebar to stop.")
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        try:
            while True:
                if keyboard.is_pressed('space'):
                    print("Recording stopped.")
                    break
                audio_data = recognizer.listen(source, timeout=10, phrase_time_limit=5)
                transcription = get_transcription_from_audio(audio_data, lang)
                print("Transcription:", transcription)
                append_transcription_to_file(transcription, output_file)
        except sr.WaitTimeoutError:
            pass

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_menu():
    while True:
        clear_console()
        print("\nSelect an option:")
        print("1. Transcribe Audio File")
        print("2. Start Live Transcription")
        
        user_choice = input("Enter your choice (1 or 2): ").strip()
        
        if user_choice == "1":
            print("Enter the path to the audio file (WAV, MP3, M4A, OGG, FLAC):")
            input_path = input().strip()
            if not os.path.isfile(input_path):
                print("Error: File not found.")
            else:
                print("Enter the path to save the output transcription:")
                output_path = input().strip()
                try:
                    transcribe_audio_file(input_path, output_path)
                except Exception as error:
                    print(f"Error: {error}")
        elif user_choice == "2":
            print("Starting live recording... Press spacebar to start and stop.")
            record_live_audio_and_transcribe()
        else:
            print("Invalid choice. Please enter 1 or 2.")

if __name__ == '__main__':
    display_menu()
