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

# Function to check for internet connection


def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        return False

# Speech Recognition Logic


class SpeechRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Recognition")
        self.root.geometry("800x600")
        self.root.configure(bg="#212121")

        # Create menu bar
        menu_bar = tk.Menu(self.root)
        file_menu = tk.Menu(menu_bar, tearoff=0, bg="#2a2a2a", fg="white")
        file_menu.add_command(label="Select File", command=self.select_file)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.quit_app)
        menu_bar.add_cascade(label="☰", menu=file_menu)
        self.root.config(menu=menu_bar)

        # Canvas to simulate a round button
        self.canvas = tk.Canvas(root, bg="#212121", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Draw round button (centered oval)
        x_center, y_center, r = 400, 250, 120
        self.btn_live_oval = self.canvas.create_oval(
            x_center - r, y_center - r, x_center + r, y_center + r,
            fill="#171717", outline=""
        )
        self.btn_live_text = self.canvas.create_text(
            x_center, y_center, text="Live Recording",
            fill="white", font=("Helvetica", 12, "bold")
        )

        # Hover effect functions
        def on_enter(event):
            self.canvas.itemconfig(
                self.btn_live_oval, fill="#2a2a2a")  # lighter shade

        def on_leave(event):
            self.canvas.itemconfig(
                self.btn_live_oval, fill="#171717")  # original color

        # Bind hover to both oval and text
        self.canvas.tag_bind(self.btn_live_oval, "<Enter>", on_enter)
        self.canvas.tag_bind(self.btn_live_oval, "<Leave>", on_leave)
        self.canvas.tag_bind(self.btn_live_text, "<Enter>", on_enter)
        self.canvas.tag_bind(self.btn_live_text, "<Leave>", on_leave)

        # Bind click events to both oval and text
        self.canvas.tag_bind(self.btn_live_oval, "<Button-1>",
                             lambda e: self.use_live_audio())
        self.canvas.tag_bind(self.btn_live_text, "<Button-1>",
                             lambda e: self.use_live_audio())

        # Frame to hold text box and scrollbar together
        text_frame = tk.Frame(root, bg="#212121")
        text_frame.place(relx=0.5, rely=0.90, anchor="center")

        # Text box
        self.text_box = tk.Text(text_frame, width=90, height=7, bg="#1e1e1e",
                                fg="white", insertbackground='white', wrap="word", bd=0)
        self.text_box.pack(side=tk.LEFT, fill=tk.BOTH)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(text_frame, command=self.text_box.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_box.config(yscrollcommand=self.scrollbar.set)

    def make_button_round(self, button):
        button.config(borderwidth=0)
        button.config(highlightthickness=0)
        button.config(font=("Helvetica", 30, "bold"))
        button.config(wraplength=120)

    def animate_button(self):
        if not hasattr(self, "recording") or not self.recording:
            return

        def audio_callback(indata, frames, time, status):
            volume_norm = np.linalg.norm(indata) * 10
            self.current_rms = volume_norm

        # Initialize once
        if not hasattr(self, "audio_stream"):
            self.current_rms = 0
            self.audio_stream = sd.InputStream(callback=audio_callback)
            self.audio_stream.start()

        # Normalize and cap scale
        scale = 1.0 + min(self.current_rms / 10.0, 1.0)
        x_center, y_center = 400, 250
        r = int(80 * scale)
        self.canvas.coords(self.btn_live_oval,
                           x_center - r, y_center - r,
                           x_center + r, y_center + r)
        self.canvas.coords(self.btn_live_text, x_center, y_center)

        self.root.after(100, self.animate_button)

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

    def display_text(self, content):
        self.text_box.delete(1.0, tk.END)
        words = content.split()
        line = "Transcription complete:\n"
        for word in words:
            if len(line) + len(word) + 1 > 75:
                self.text_box.insert(tk.END, line + '\n')
                line = word
            else:
                if line:
                    line += " " + word
                else:
                    line = word
        if line:
            self.text_box.insert(tk.END, line + '\n')

    def read_wav(self, file_path):
        try:
            # wav_file = SpeechRec.prepare_voice_file(file_path)
            if check_internet_connection():
                text = SpeechRec().transcribe_audio_file(file_path, "output.txt")
            else:
                # Initialize offline recognizer
                self.offline_recognizer = OfflineSpeechRecognition(
                    r"C:\Users\matth\Downloads\vosk-model-en-us-0.42-gigaspeech")
                converted_path = self.offline_recognizer.convert_to_wav_mono_pcm(
                    wav_file)
                text = self.offline_recognizer.transcribe_audio_file(
                    converted_path)
            self.display_text(text)
        except Exception as e:
            self.display_text(f"Error processing WAV file: {e}")

    def read_text(self, file_path):
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            self.display_text(f"Transcription:\n{content}")
        except Exception as e:
            self.display_text(f"Error reading text file: {e}")

    def use_live_audio(self):
        if hasattr(self, 'recording') and self.recording:
            # Stop recording
            self.recording = False
            if hasattr(self, "audio_stream"):
                self.audio_stream.stop()
                self.audio_stream.close()
                del self.audio_stream
            self.canvas.itemconfig(self.btn_live_text, text="Live Recording")
        else:
            # Start recording
            self.recording = True
            self.canvas.itemconfig(self.btn_live_text, text="Stop Recording")
            # self.animate_button()
            threading.Thread(target=self.record_audio).start()

    def record_audio(self):

        self.display_text("Recording... Press 'Stop Recording' to finish.")
        fs = 44100  # Sample rate
        seconds = 0  # Duration is dynamic based on button press
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

        # Save the recording
        audio_array = np.concatenate(audio_data, axis=0)
        write("live_recording.wav", fs, (audio_array * 32767).astype(np.int16))
        self.display_text("Recording saved as 'live_recording.wav'.")
        # Process the saved recording
        try:
            if check_internet_connection():
                text = SpeechRec().transcribe_audio_file("live_recording.wav", "output.txt")
            else:
                # Initialize offline recognizer
                self.offline_recognizer = OfflineSpeechRecognition(
                    r"C:\Users\matth\Downloads\vosk-model-en-us-0.42-gigaspeech")
                converted_path = self.offline_recognizer.convert_to_wav_mono_pcm(
                    "live_recording.wav")
                text = self.offline_recognizer.transcribe_audio_file(
                    converted_path)
            self.display_text(text)
        except Exception as e:
            self.display_text(f"Error processing live recording: {e}")

    def quit_app(self):
        self.root.quit()


if __name__ == "__main__":
    # Run the application
    root = tk.Tk()
    app = SpeechRecognitionApp(root)
    root.mainloop()
