import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import os
import speech_recognition as sr
from speech_to_text import SpeechRec
from offline_speech_recognition import OfflineSpeechRecognition
import socket

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

        # Load and display the image
        self.image_path = "logo.png"  # Ensure this file is in the same directory
        self.image = Image.open(self.image_path)
        self.image = self.image.resize((600, 500), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.image)

        self.canvas = tk.Canvas(root, width=600, height=500)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)

        # Buttons inside the image
        self.btn_select = tk.Button(
            root, text="Select File", command=self.select_file, width=20, height=2)
        self.btn_live = tk.Button(
            root, text="Live Recording", command=self.use_live_audio, width=20, height=2)
        self.btn_quit = tk.Button(
            root, text="Quit", command=self.quit_app, width=20, height=2)

        # Positioning buttons over the image
        self.canvas.create_window(165, 150, window=self.btn_select)
        self.canvas.create_window(165, 235, window=self.btn_live)
        self.canvas.create_window(165, 321, window=self.btn_quit)

        # Add a Text widget for transcription display
        self.text_box = tk.Text(root, width=70, height=6.5, wrap=tk.WORD)

        # Add a Scrollbar widget
        self.scrollbar = tk.Scrollbar(
            root, orient=tk.VERTICAL, command=self.text_box.yview)

        # Configure the Text widget to work with the Scrollbar
        self.text_box.configure(yscrollcommand=self.scrollbar.set)

        # Position the Text widget and Scrollbar on the canvas
        # Positioning the text box
        self.canvas.create_window(300, 420, window=self.text_box)
        # Positioning the scrollbar next to the text box
        self.canvas.create_window(590, 420, window=self.scrollbar)

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
        line = ""
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
            wav_file = SpeechRec.prepare_voice_file(file_path)
            if check_internet_connection():
                text = SpeechRec.speech_to_text(
                    wav_file, "output.txt", "en-US")
            else:
                # Initialize offline recognizer
                self.offline_recognizer = OfflineSpeechRecognition(
                    r"C:\Users\matth\Downloads\vosk-model-en-us-0.42-gigaspeech")
                converted_path = self.offline_recognizer.convert_to_wav_mono_pcm(
                    wav_file)
                text = self.offline_recognizer.transcribe_audio_file(
                    converted_path)
            self.display_text(f"Transcription:\n{text}")
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
        self.display_text("Using live audio")

    def quit_app(self):
        self.root.quit()


# Run the application
root = tk.Tk()
app = SpeechRecognitionApp(root)
root.mainloop()
