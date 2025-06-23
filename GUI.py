import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import speech_recognition as sr
from speech_to_text import SpeechRec
from offline_speech_recognition import OfflineSpeechRecognition
import socket
import keyboard
import threading
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import librosa
import parselmouth
import re
import wave

from vosk import Model, KaldiRecognizer
from pyannote.audio import Pipeline
from pydub import AudioSegment

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization",
    use_auth_token="temp_key_here"
)


def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False


class SpeechRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Recognition")
        self.root.geometry("800x600")
        self.root.configure(bg="#212121")
        self.speaker_colors = {}  # <- FIXED: Declare once here

        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=0, bg="#2a2a2a", fg="white")
        file_menu.add_command(label="Select File", command=self.select_file)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.quit_app)
        menu_bar.add_cascade(label="☰", menu=file_menu)
        self.root.config(menu=menu_bar)

        self.canvas = tk.Canvas(root, bg="#212121", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        x_center, y_center, r = 400, 250, 120
        self.btn_live_oval = self.canvas.create_oval(
            x_center - r, y_center - r, x_center + r, y_center + r,
            fill="#171717", outline=""
        )
        self.btn_live_text = self.canvas.create_text(
            x_center, y_center, text="Live Recording",
            fill="white", font=("Helvetica", 12, "bold")
        )

        def on_enter(event):
            self.canvas.itemconfig(self.btn_live_oval, fill="#2a2a2a")

        def on_leave(event):
            self.canvas.itemconfig(self.btn_live_oval, fill="#171717")

        self.canvas.tag_bind(self.btn_live_oval, "<Enter>", on_enter)
        self.canvas.tag_bind(self.btn_live_oval, "<Leave>", on_leave)
        self.canvas.tag_bind(self.btn_live_text, "<Enter>", on_enter)
        self.canvas.tag_bind(self.btn_live_text, "<Leave>", on_leave)
        self.canvas.tag_bind(self.btn_live_oval, "<Button-1>",
                             lambda e: self.use_live_audio())
        self.canvas.tag_bind(self.btn_live_text, "<Button-1>",
                             lambda e: self.use_live_audio())

        text_frame = tk.Frame(root, bg="#212121")
        text_frame.place(relx=0.5, rely=0.90, anchor="center")

        self.text_box = tk.Text(text_frame, width=90, height=7, bg="#1e1e1e",
                                fg="white", insertbackground='white', wrap="word", bd=0)
        self.text_box.pack(side=tk.LEFT, fill=tk.BOTH)

        self.scrollbar = tk.Scrollbar(text_frame, command=self.text_box.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_box.config(yscrollcommand=self.scrollbar.set)

    def display_text(self, content, tag=None, append=False):
        if not append:
            self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, content + "\n", tag)

    def select_file(self, hidden=False):
        initial_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = filedialog.askopenfilename(initialdir=initial_dir)
        if file_path:
            if hidden:
                self.read_text(file_path)
            else:
                self.read_wav(file_path)
        else:
            self.display_text("No file selected")

    def read_wav(self, file_path):
        try:
            diarization = pipeline(file_path)
            self.text_box.delete(1.0, tk.END)
            self.text_box.insert(tk.END, "Detected Speakers:\n\n")
            self.speaker_colors = {}
            color_palette = ["skyblue", "lightgreen",
                             "salmon", "violet", "orange", "lightgray"]
            color_index = 0

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                start = turn.start
                end = turn.end

                audio = AudioSegment.from_wav(file_path)
                segment = audio[start * 1000:end * 1000]
                segment_path = "temp_segment.wav"
                segment.export(segment_path, format="wav")

                if check_internet_connection():
                    text = SpeechRec().transcribe_audio_file(segment_path, "output.txt")
                else:
                    self.offline_recognizer = OfflineSpeechRecognition(
                        r"C:\\Users\\matth\\Downloads\\vosk-model-en-us-0.42-gigaspeech")
                    converted_path = self.offline_recognizer.convert_to_wav_mono_pcm(
                        segment_path)
                    text = self.offline_recognizer.transcribe_audio_file(
                        converted_path)

                if speaker not in self.speaker_colors:
                    tag = f"speaker_{len(self.speaker_colors)}"
                    self.speaker_colors[speaker] = tag
                    self.text_box.tag_config(
                        tag, foreground=color_palette[color_index % len(color_palette)])
                    color_index += 1

                tag = self.speaker_colors[speaker]
                self.text_box.insert(tk.END, f"[{speaker}] ", tag)
                self.text_box.insert(tk.END, text.strip() + "\n", tag)

            self.text_box.insert(tk.END, "\nTranscription complete.")
        except Exception as e:
            self.display_text(
                f"Error processing WAV file with diarization: {e}")

    def read_text(self, file_path):
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            self.display_text(f"Transcription:\n{content}")
        except Exception as e:
            self.display_text(f"Error reading text file: {e}")

    def use_live_audio(self):
        if hasattr(self, 'recording') and self.recording:
            self.recording = False
            if hasattr(self, "audio_stream"):
                self.audio_stream.stop()
                self.audio_stream.close()
                del self.audio_stream
            self.canvas.itemconfig(self.btn_live_text, text="Live Recording")
        else:
            self.recording = True
            self.canvas.itemconfig(self.btn_live_text, text="Stop Recording")
            threading.Thread(target=self.record_audio).start()

    def record_audio(self):
        self.display_text("Recording... Press 'Stop Recording' to finish.")
        fs = 44100
        audio_data = []

        def callback(indata, frames, time, status):
            if self.recording:
                audio_data.append(indata.copy())
            else:
                raise sd.CallbackStop()

        try:
            with sd.InputStream(samplerate=fs, channels=1, callback=callback):
                while self.recording:
                    sd.sleep(100)
        except Exception as e:
            self.display_text(f"Error during recording: {e}")
            return

        audio_array = np.concatenate(audio_data, axis=0)
        write("live_recording.wav", fs, (audio_array * 32767).astype(np.int16))
        self.display_text("Recording saved. Processing...", append=True)

        try:
            diarization = pipeline("live_recording.wav")
            self.text_box.delete(1.0, tk.END)
            self.text_box.insert(tk.END, "Detected Speakers:\n\n")
            self.speaker_colors = {}
            color_palette = ["skyblue", "lightgreen",
                             "salmon", "violet", "orange", "lightgray"]
            color_index = 0

            audio = AudioSegment.from_wav("live_recording.wav")

            for turn, _, speaker in diarization.itertracks(yield_label=True):
                start = turn.start
                end = turn.end

                segment = audio[start * 1000:end * 1000]
                segment_path = "temp_segment.wav"
                segment.export(segment_path, format="wav")

                if check_internet_connection():
                    text = SpeechRec().transcribe_audio_file(segment_path, "output.txt")
                else:
                    self.offline_recognizer = OfflineSpeechRecognition(
                        r"C:\\Users\\matth\\Downloads\\vosk-model-en-us-0.42-gigaspeech")
                    converted_path = self.offline_recognizer.convert_to_wav_mono_pcm(
                        segment_path)
                    text = self.offline_recognizer.transcribe_audio_file(
                        converted_path)

                if speaker not in self.speaker_colors:
                    tag = f"speaker_{len(self.speaker_colors)}"
                    self.speaker_colors[speaker] = tag
                    self.text_box.tag_config(
                        tag, foreground=color_palette[color_index % len(color_palette)])
                    color_index += 1

                tag = self.speaker_colors[speaker]
                self.text_box.insert(tk.END, f"[{speaker}] ", tag)
                self.text_box.insert(tk.END, text.strip() + "\n", tag)

            self.text_box.insert(tk.END, "\nTranscription complete.")
        except Exception as e:
            self.display_text(f"Error processing live recording: {e}")

    def quit_app(self):
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpeechRecognitionApp(root)
    root.mainloop()
