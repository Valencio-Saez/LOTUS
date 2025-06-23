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
from tkinter import messagebox
import json
from pydub import AudioSegment
import sys
import queue
from vosk import KaldiRecognizer

# Ensure speech_recognition can find flac.exe when bundled
if getattr(sys, 'frozen', False):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    os.environ['FLAC_EXECUTABLE'] = os.path.join(base_path, 'flac.exe')
else:
    os.environ['FLAC_EXECUTABLE'] = 'flac.exe'

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

        self.transcription_queue = queue.Queue()
        self.transcription_running = False

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
        """Process WAV file in 4-second segments with 0.5s overlap and simple post-processing to remove repeated words."""
        try:
            if check_internet_connection():
                # Online: transcribe entire file at once
                text = self.transcribe_entire_file_online(file_path)
                if text and text.strip() and text.strip() != '[Could not understand audio]':
                    self.display_text(text)
                else:
                    self.display_text("No speech detected in the audio file.")
            else:
                # Offline: transcribe entire file at once
                text = self.transcribe_entire_file_offline(file_path)
                if text and text.strip() and text.strip() != '[Could not understand audio]':
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
            self._last_live_text = ""
            if hasattr(self, 'lotus_open_photo'):
                self.btn_live.config(image=self.lotus_open_photo)
            threading.Thread(target=self.record_audio, daemon=True).start()

    def record_audio(self):
        """Record audio from microphone and transcribe in 4-second segments (VOSK if offline)"""
        fs = 16000  # VOSK expects 16kHz
        segment_duration = 4  # seconds per segment
        if getattr(sys, 'frozen', False):
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        vosk_model_path = os.path.join(base_path, "vosk-model-en-us-0.42-gigaspeech")

        if check_internet_connection():
            # Online: record and transcribe every 4 seconds in real time, but transcribe in main thread
            audio_queue = queue.Queue()
            stop_flag = threading.Event()

            def audio_callback(indata, frames, time, status):
                if self.recording:
                    audio_queue.put(indata.copy())
                else:
                    stop_flag.set()
                    raise sd.CallbackStop()

            def segment_producer():
                buffer = []
                samples_per_segment = int(44100 * segment_duration)
                overlap_samples = int(44100 * 0.5)  # 0.5s overlap
                step = samples_per_segment - overlap_samples
                while self.recording or not audio_queue.empty():
                    try:
                        data = audio_queue.get(timeout=0.1)
                        buffer.extend(data.flatten())
                        while len(buffer) >= samples_per_segment:
                            segment = np.array(buffer[:samples_per_segment])
                            buffer = buffer[step:]
                            write("live_recording_segment.wav", 44100, (segment * 32767).astype(np.int16))
                            self.transcription_queue.put("live_recording_segment.wav")
                    except queue.Empty:
                        continue
                # Process any remaining buffer after recording stops
                if buffer:
                    segment = np.array(buffer)
                    write("live_recording_segment.wav", 44100, (segment * 32767).astype(np.int16))
                    self.transcription_queue.put("live_recording_segment.wav")

            # Create a queue for transcription tasks
            self.transcription_queue = queue.Queue()

            def transcription_consumer_mainthread():
                try:
                    while not self.transcription_queue.empty():
                        wav_path = self.transcription_queue.get()
                        with sr.AudioFile(wav_path) as source:
                            audio_data = sr.Recognizer().record(source)
                            text = SpeechRec().get_transcription_from_audio(audio_data)
                        if text and text.strip() and text.strip() != '[Could not understand audio]':
                            # Simple post-processing: remove repeated words at boundary
                            if hasattr(self, '_last_live_text'):
                                split_last = self._last_live_text.strip().split()
                                split_text = text.strip().split()
                                overlap_len = min(3, len(split_last), len(split_text))
                                for j in range(overlap_len, 0, -1):
                                    if split_last[-j:] == split_text[:j]:
                                        text = ' '.join(split_text[j:])
                                        break
                            self.display_text(text)
                            self._last_live_text = text
                except Exception as e:
                    self.display_text(f"Error during transcription: {str(e)}")
                if self.recording or not self.transcription_queue.empty():
                    self.root.after(100, transcription_consumer_mainthread)

            try:
                with sd.InputStream(samplerate=44100, channels=1, callback=audio_callback):
                    producer_thread = threading.Thread(target=segment_producer, daemon=True)
                    producer_thread.start()
                    self.root.after(100, transcription_consumer_mainthread)
                    while self.recording and not stop_flag.is_set():
                        sd.sleep(100)
                    producer_thread.join()
            except Exception as e:
                self.display_text(f"Error during recording: {str(e)}")
                return
            return
        else:
            # Offline: VOSK segment/streaming transcription
            if not os.path.exists(vosk_model_path):
                messagebox.showerror("VOSK Model Missing", "Need to download VOSK model")
                return
            try:
                self.offline_recognizer = OfflineSpeechRecognition(vosk_model_path)
                model = self.offline_recognizer.model
                recognizer = KaldiRecognizer(model, fs)
                q = queue.Queue()
                def callback(indata, frames, time, status):
                    if self.recording:
                        q.put(bytes(indata))
                    else:
                        raise sd.CallbackStop()
                with sd.RawInputStream(samplerate=fs, blocksize = int(fs * segment_duration), dtype='int16', channels=1, callback=callback):
                    last_partial = ""
                    while self.recording:
                        try:
                            data = q.get(timeout=0.5)
                        except queue.Empty:
                            continue
                        if recognizer.AcceptWaveform(data):
                            res = recognizer.Result()
                            text = json.loads(res).get("text", "")
                            if text:
                                self.display_text(text)
                                last_partial = ""
                        else:
                            partial = recognizer.PartialResult()
                            partial_text = json.loads(partial).get("partial", "")
                            if partial_text and partial_text != last_partial:
                                self.display_text(partial_text)
                                last_partial = partial_text
            except Exception as e:
                messagebox.showerror("VOSK Error", f"Error initializing or using VOSK model: {str(e)}")
                self.display_text(f"Error processing live recording: {str(e)}")
                return

    def add_segment_to_queue(self, segment_path):
        self.transcription_queue.put(segment_path)
        if not self.transcription_running:
            self.process_next_transcription()

    def process_next_transcription(self):
        if not self.transcription_queue.empty():
            self.transcription_running = True
            segment_path = self.transcription_queue.get()
            # Do transcription (in main thread or a single background thread)
            # When done:
            self.root.after(0, self.process_next_transcription)
        else:
            self.transcription_running = False

    def transcribe_entire_file_online(self, file_path):
        """Transcribe entire audio file using Google Speech Recognition (online)"""
        try:
            with sr.AudioFile(file_path) as source:
                audio_data = sr.Recognizer().record(source)
                return SpeechRec().get_transcription_from_audio(audio_data)
        except Exception as e:
            self.display_text(f"Error in online transcription: {str(e)}")
            return ""

    def transcribe_entire_file_offline(self, file_path):
        """Transcribe entire audio file using VOSK (offline)"""
        try:
            if getattr(sys, 'frozen', False):
                base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            vosk_model_path = os.path.join(base_path, "vosk-model-en-us-0.42-gigaspeech")
            if not os.path.exists(vosk_model_path):
                messagebox.showerror("VOSK Model Missing", "Need to download VOSK model")
                return ""
            
            self.offline_recognizer = OfflineSpeechRecognition(vosk_model_path)
            converted_path = self.offline_recognizer.convert_to_wav_mono_pcm(file_path)
            text = self.offline_recognizer.transcribe_audio_file(converted_path)
            return text
        except Exception as e:
            messagebox.showerror("VOSK Error", f"Error initializing or using VOSK model: {str(e)}")
            self.display_text(f"Error in offline transcription: {str(e)}")
            return ""

if __name__ == "__main__":
    # Run the application
    root = tk.Tk()
    app = SpeechRecognitionApp(root)
    root.mainloop()
