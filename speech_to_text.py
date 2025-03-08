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
        raise ValueError(f'Unsupported audio format: {format(os.path.splitext(path)[1])}')


def transcribe_audio(audio_data, language) -> str:
    """
    Transcribes audio data to text using Google's speech recognition API.
    """
    r = sr.Recognizer()
    text = r.recognize_google(audio_data, language=language)
    return text


def write_transcription_to_file(text, output_file) -> None:
    """
    Writes the transcribed text to the output file.
    """
    with open(output_file, 'w') as f:
        f.write(text)


def speech_to_text(language: str = "en-US") -> None:
    """
    Transcribes the audio to text and writes the text to a file.
    Starts recording when spacebar is pressed, and stops when spacebar is pressed again.
    """
    r = sr.Recognizer()
    
    recording = False
    with sr.Microphone() as source:

        print("LOTUS: SPEECH TO TEXT APPLICATION")

        print("Ambient noise detected. Adjustments complete. Ready to record!")
        
        print("\nPress spacebar to start recording. Press it again to stop.")

        r.adjust_for_ambient_noise(source)  # Adjusting for ambient noise
        
        # Wait until spacebar is pressed to start recording
        while True:
            if keyboard.is_pressed('space'):  # Wait for spacebar press
                if not recording:
                    print("Recording started...")
                    recording = True
                    print("Recording... Speak now!")
                    audio_data = r.listen(source, timeout=20, phrase_time_limit=10)  # Start recording
                    print("Recording stopped.")
                    text = transcribe_audio(audio_data, language)  # Transcribe audio to text
                    print("Transcription:", text)
                    write_transcription_to_file(text, "output.txt")  # Save to file
                    break  # Break out of loop after one recording
                else:
                    print("Recording stopped.")
                    break  # Stop recording when space is pressed again
            

if __name__ == '__main__':
    speech_to_text()  # Start the process with the default language ("en-US")
