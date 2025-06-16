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
        self.root.geometry("900x600")
        self.root.configure(bg="#fff")  # White background

        # Header Frame
        header = tk.Frame(root, bg="#ffb6c1", height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header_label = tk.Label(
            header,
            text="LOTUS Speech Recognition",
            font=("Arial", 22, "bold"),
            fg="white",
            bg="#ffb6c1"
        )
        header_label.pack(pady=10)

        # Main Frame
        main_frame = tk.Frame(root, bg="#fff")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar for buttons
        sidebar = tk.Frame(main_frame, bg="#ffe4ec", width=200)
        sidebar.pack(fill=tk.Y, side=tk.LEFT)
        sidebar.pack_propagate(False)

        self.btn_select = tk.Button(
            sidebar, text="Select File", command=self.select_file,
            width=18, height=2, bg="#ffb6c1", fg="white",
            font=("Arial", 12, "bold"), activebackground="#ff69b4", activeforeground="white"
        )
        self.btn_select.pack(pady=(40, 20))

        self.btn_quit = tk.Button(
            sidebar, text="Quit", command=self.quit_app,
            width=18, height=2, bg="#ff69b4", fg="white",
            font=("Arial", 12, "bold"), activebackground="#ffb6c1", activeforeground="white"
        )
        self.btn_quit.pack(pady=20)

        # Content area
        content = tk.Frame(main_frame, bg="#fff")
        content.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Load lotus images
        self.lotus_closed_img = Image.open("lotusclosed.png").resize((180, 180), Image.LANCZOS)
        self.lotus_closed_photo = ImageTk.PhotoImage(self.lotus_closed_img)
        self.lotus_open_img = Image.open("lotusopen.png").resize((180, 180), Image.LANCZOS)
        self.lotus_open_photo = ImageTk.PhotoImage(self.lotus_open_img)

        # Big live recording button in the center
        self.live_btn_frame = tk.Frame(content, bg="#fff")
        self.live_btn_frame.pack(pady=(30, 10))
        self.btn_live = tk.Button(
            self.live_btn_frame,
            image=self.lotus_closed_photo,
            command=self.use_live_audio,
            bd=0,
            bg="#fff",
            activebackground="#fff"
        )
        self.btn_live.pack()

        # Transcription box with scrollbar
        text_frame = tk.Frame(content, bg="#fff")
        text_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        self.text_box = tk.Text(
            text_frame, width=60, height=12, wrap=tk.WORD,
            font=("Arial", 12), bg="#ffe4ec", fg="#c71585", insertbackground="#c71585"
        )
        self.text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_box.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_box.configure(yscrollcommand=self.scrollbar.set)

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
            self.btn_live.config(image=self.lotus_closed_photo)
        else:
            # Start recording
            self.recording = True
            self.btn_live.config(image=self.lotus_open_photo)
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
                converted_path = self.offline_recognizer.convert_to_wav_mono_pcm("live_recording.wav")
                text = self.offline_recognizer.transcribe_audio_file(converted_path)
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
