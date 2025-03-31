import os
import wave
import json
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment


class OfflineSpeechRecognition:
    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model path not found: {model_path}")
        self.model = Model(model_path)

    def convert_to_wav_mono_pcm(self, audio_path: str) -> str:
        """
        Converts the input audio file to WAV format mono PCM with a sample rate of 16000 Hz.
        """
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        wav_path = os.path.splitext(audio_path)[0] + "_converted.wav"
        audio.export(wav_path, format="wav")
        return wav_path

    def transcribe_audio_file(self, audio_path: str) -> str:
        """
        Transcribes a pre-recorded audio file using VOSK.
        """
        recognizer = KaldiRecognizer(self.model, 16000)

        with wave.open(audio_path, "rb") as wf:
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                recognizer.AcceptWaveform(data)

        return json.loads(recognizer.FinalResult())["text"]


if __name__ == '__main__':
    MODEL_PATH = r"C:\Users\Frank\github lotus\LOTUS\LOTUS\vosk-model-en-us-0.42-gigaspeech\vosk-model-en-us-0.42-gigaspeech"
    recognizer = OfflineSpeechRecognition(MODEL_PATH)

    print('Enter the path to an audio file:')
    input_path = input().strip()

    if not os.path.isfile(input_path):
        print('Error: File not found.')
    else:
        try:
            converted_path = recognizer.convert_to_wav_mono_pcm(input_path)
            text = recognizer.transcribe_audio_file(converted_path)
            print("Transcription:")
            print(text)
        except Exception as e:
            print("Error:", e)
