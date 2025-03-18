import tkinter as tk
from tkinter import filedialog, scrolledtext
import os


class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("My GUI")
        self.root.geometry("600x600")
        self.root.configure(bg="black")
        # Update with the correct path to your icon
        # self.root.iconbitmap("path/to/speaker/icon.ico")

        self.button_style = {
            "bg": "black",
            "fg": "light blue",
            "font": ("Helvetica", 12, "bold"),
            "highlightbackground": "light blue",
            "highlightcolor": "light blue",
            "highlightthickness": 2,
            "bd": 10
        }

        self.create_widgets()

    def create_widgets(self):
        btn_select_file = tk.Button(self.root, text="Select File",
                                    command=self.select_file, **self.button_style)
        btn_select_file.pack(pady=10)

        btn_use_live_audio = tk.Button(
            self.root, text="Use Live Audio", command=self.use_live_audio, **self.button_style)
        btn_use_live_audio.pack(pady=10)

        btn_quit = tk.Button(self.root, text="Quit",
                             command=self.quit_app, **self.button_style)
        btn_quit.pack(pady=10)

        self.text_box = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, width=70, height=20, bg="black", fg="light blue", font=("Helvetica", 12), bd=0, highlightthickness=0)
        self.text_box.pack(pady=10, padx=10)

        # Hidden button in the top left corner
        self.hidden_button = tk.Button(
            self.root, command=lambda: self.select_file(hidden=True), bg="black", width=10, height=2, bd=0, highlightthickness=0)
        self.hidden_button.place(x=0, y=0)
        self.hidden_button.lower()

    def select_file(self, hidden=False):
        initial_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = filedialog.askopenfilename(initialdir=initial_dir)
        if file_path:
            if hidden:
                self.hidden_button_action(file_path)
            else:
                self.read_wav(file_path)
        else:
            self.display_text("No file selected")

    def read_wav(self, file_path):
        if os.path.splitext(file_path)[1].lower() == '.wav':
            with open(file_path, 'r') as file:
                content = file.read()
            self.display_text(content)
        else:
            self.display_text("Invalid File: Please select a .wav file.")
            self.text_box.tag_add("error", "1.0", "end")
            self.text_box.tag_config("error", foreground="red")

    def hidden_button_action(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        self.display_text(content)

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

    def use_live_audio(self):
        print("Using live audio")

    def quit_app(self):
        self.root.quit()


if __name__ == "__main__":
    window = tk.Tk()
    gui = GUI(window)
    window.mainloop()
