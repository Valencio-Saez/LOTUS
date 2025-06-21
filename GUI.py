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

class SpeechRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LOTUS")
        self.root.geometry("900x600")
        self.root.configure(bg="#fff")
        
        # Initialize recording state
        self.recording = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header Frame
        header = tk.Frame(self.root, bg="#ffb6c1", height=60)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        
        header_label = tk.Label(
            header,
            text="LOTUS",
            font=("Segoe UI", 22, "bold"),
            fg="white",
            bg="#ffb6c1"
        )
        header_label.pack(pady=10)

        # Main Frame
        main_frame = tk.Frame(self.root, bg="#fff")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Content area (center everything)
        content = tk.Frame(main_frame, bg="#fff")
        content.pack(fill=tk.BOTH, expand=True)

        # Select File button (small, top center)
        try:
            self.sidebar_img = Image.open("sidebar.png").resize((40, 40), Image.Resampling.LANCZOS)
            self.sidebar_photo = ImageTk.PhotoImage(self.sidebar_img)
            self.btn_select = tk.Button(
                content, image=self.sidebar_photo, command=self.select_file,
                bd=0, bg="#fff", activebackground="#fff", cursor="hand2",
                width=40, height=40
            )
        except:
            self.btn_select = tk.Button(
                content, text="📁", command=self.select_file,
                bd=0, bg="#fff", activebackground="#fff", cursor="hand2",
                font=("Segoe UI", 16), width=3, height=2
            )
        self.btn_select.pack(pady=(20, 10))

        # Lotus images and big live recording button (center)
        try:
            self.lotus_closed_img = Image.open("lotusclosed.png").resize((180, 180), Image.Resampling.LANCZOS)
            self.lotus_closed_photo = ImageTk.PhotoImage(self.lotus_closed_img)
            self.lotus_open_img = Image.open("lotusopen.png").resize((180, 180), Image.Resampling.LANCZOS)
            self.lotus_open_photo = ImageTk.PhotoImage(self.lotus_open_img)
            
            self.btn_live = tk.Button(
                content,
                image=self.lotus_closed_photo,
                command=self.use_live_audio,
                bd=0,
                bg="#fff",
                activebackground="#fff"
            )
        except:
            self.btn_live = tk.Button(
                content,
                text="🎤",
                command=self.use_live_audio,
                bd=0,
                bg="#fff",
                activebackground="#fff",
                font=("Segoe UI", 48),
                width=8, height=8
            )
        self.btn_live.pack(pady=(10, 20))

        # Transcription box with scrollbar (centered below)
        text_frame = tk.Frame(content, bg="#fff")
        text_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        self.text_box = tk.Text(
            text_frame, width=60, height=12, wrap=tk.WORD,
            font=("Segoe UI", 13), bg="#ffe4ec", fg="#c71585", insertbackground="#c71585"
        )
        self.text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_box.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_box.configure(yscrollcommand=self.scrollbar.set)

    def select_file(self):
        """Select and process an audio file"""
        file_types = [
            ("Audio files", "*.wav *.mp3 *.m4a *.flac"),
            ("WAV files", "*.wav"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=file_types,
            initialdir=os.path.dirname(os.path.abspath(__file__))
        )
        
        if file_path:
            self.read_wav(file_path)
        else:
            self.display_text("No file selected")

    def display_text(self, content):
        """Display transcription text"""
        self.text_box.insert(tk.END, content.strip() + '\n\n')
        self.text_box.see(tk.END)

    def read_wav(self, file_path):
        """Process WAV file with error handling"""
        try:
            if check_internet_connection():
                text = SpeechRec().transcribe_audio_file(file_path, "output.txt")
            else:
                # Initialize offline recognizer
                self.offline_recognizer = OfflineSpeechRecognition(
                    r"C:\Users\matth\Downloads\vosk-model-en-us-0.42-gigaspeech")
                converted_path = self.offline_recognizer.convert_to_wav_mono_pcm(file_path)
                text = self.offline_recognizer.transcribe_audio_file(converted_path)
            
            if text and text.strip():
                self.display_text(text)
            else:
                self.display_text("No speech detected in the audio file.")
                
        except Exception as e:
            self.display_text(f"Error processing audio file: {str(e)}")

    def use_live_audio(self):
        """Toggle live audio recording"""
        if self.recording:
            # Stop recording
            self.recording = False
            if hasattr(self, 'lotus_closed_photo'):
                self.btn_live.config(image=self.lotus_closed_photo)
        else:
            # Start recording
            self.recording = True
            if hasattr(self, 'lotus_open_photo'):
                self.btn_live.config(image=self.lotus_open_photo)
            threading.Thread(target=self.record_audio, daemon=True).start()

    def record_audio(self):
        """Record audio from microphone"""
        fs = 44100  # Sample rate
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
            self.display_text(f"Error during recording: {str(e)}")
            return

        if not audio_data:
            return

        # Save the recording
        try:
            audio_array = np.concatenate(audio_data, axis=0)
            write("live_recording.wav", fs, (audio_array * 32767).astype(np.int16))
            
            # Process the saved recording
            if check_internet_connection():
                text = SpeechRec().transcribe_audio_file("live_recording.wav", "output.txt")
            else:
                # Initialize offline recognizer
                self.offline_recognizer = OfflineSpeechRecognition(
                    r"C:\Users\matth\Downloads\vosk-model-en-us-0.42-gigaspeech")
                converted_path = self.offline_recognizer.convert_to_wav_mono_pcm("live_recording.wav")
                text = self.offline_recognizer.transcribe_audio_file(converted_path)
            
            if text and text.strip():
                self.display_text(text)
            else:
                self.display_text("No speech detected in the recording.")
                
        except Exception as e:
            self.display_text(f"Error processing live recording: {str(e)}")

if __name__ == "__main__":
    # Run the application
    root = tk.Tk()
    app = SpeechRecognitionApp(root)
    root.mainloop()
