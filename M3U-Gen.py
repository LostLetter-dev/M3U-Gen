import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
import math
import os
import requests
import tempfile
import urllib.parse as p
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from time import time

class FileSelector(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("M3U Generator")
        self.geometry("500x450")

        self.create_widgets()
        self.apply_theme()

        self.items = []

    def create_widgets(self): # basic widgets, not doing anything special with these
        # Frame for buttons
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(pady=10)

        #File button
        self.add_file_button = ttk.Button(self.button_frame, text="Add File", command=self.add_file)
        self.add_file_button.pack(side=tk.LEFT, padx=5)

        #Folder button
        self.add_folder_button = ttk.Button(self.button_frame, text="Add Folder", command=self.add_folder)
        self.add_folder_button.pack(side=tk.LEFT, padx=5)

        #URL button
        self.add_url_button = ttk.Button(self.button_frame, text="Add URL", command=self.add_url)
        self.add_url_button.pack(side=tk.LEFT, padx=5)

        # listbox displays selected files and folders
        self.file_listbox = tk.Listbox(self, width=80, height=15)
        self.file_listbox.pack(pady=20)

        # delete key removes entries
        self.file_listbox.bind("<Delete>", self.remove_selected)

        # Generate button
        self.generate_button = ttk.Button(self, text="Generate", command=self.generate)
        self.generate_button.pack(pady=10)

    def add_file(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.mp3 *.wav"), ("All Files", "*.*")]) # limit selection to wav / mp3s
        for file_path in file_paths:
            if file_path:
                self.file_listbox.insert(tk.END, file_path)
                self.items.append(file_path)

    def add_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.recursive_add(folder_path)

    def add_url(self):
        url = simpledialog.askstring("Input", "Enter URL:")
        if url:
            self.file_listbox.insert(tk.END, url)
            self.items.append(url)

    def remove_selected(self, event):
        selected_indices = self.file_listbox.curselection()
        for index in selected_indices[::-1]:  # Iterate in reverse to avoid index shifting
            self.file_listbox.delete(index)
            del self.items[index]

    def generate(self):
        output_path = filedialog.asksaveasfilename(defaultextension=".m3u",
                                                   filetypes=[("M3U Playlist", "*.m3u"), ("All Files", "*.*")])
        if output_path:
            results = self.process_items()
            self.write_files(results, output_path)
            messagebox.showinfo("Success", "Playlist generated successfully!")

    def apply_theme(self):
        style = ttk.Style(self)
        style.theme_use('classic') # using classic for better cross compat 
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.configure("TFrame", background="#333")
        style.configure("TLabel", background="#333", foreground="#fff")
        self.configure(background='#333')

    def recursive_add(self, folder_path): # leftover from v1, adds all files found in a directory (so long as they are valid) recursively
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(('.mp3', '.wav')):
                    file_path = os.path.join(root, file)
                    self.file_listbox.insert(tk.END, file_path)
                    self.items.append(file_path)

    def process_items(self):
        start = time()
        results = []
        total_items = len(self.items)
        for index, item in enumerate(self.items):
            if item.startswith('http://') or item.startswith('https://'): # handle URLs specifically
                response = requests.get(item) # will freeze program for a long time with large files
                if response.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=True) as tmp:
                        tmp.write(response.content) # write recieved data into temporary file (deletes self when process terminates)
                        tmp_filepath = tmp.name
                        audio = self.get_audio(tmp_filepath)
                        results.append(newAudio(audio, item, os.path.basename(item)))
                else:
                    print("Error: ", response.status_code)
            else:
                audio = self.get_audio(item)
                results.append(newAudio(audio, item, os.path.basename(item)))
        end = time()
        print(f"Time elapsed: {math.trunc(end - start)}s")
        return results

    def get_audio(self, file_path):
        try:
            return MP3(file_path)
        except:
            try:
                return WAVE(file_path)
            except:
                raise ValueError("Unsupported file type") # will crash the program

    def write_files(self, results, output_path): # write M3U file in proper formatting
        with open(output_path, "wt") as f:
            f.write("#EXTM3U\n\n")
            for item in results:
                f.write(f"#EXTINF:{item.length},Author - {item.title}\n{item.link}\n\n")


class newAudio:
    def __init__(self, audio, link, name):
        self.title = name
        self.link = link
        self.audio = audio
        self.length = int(audio.info.length)  # Gets length of audio in seconds


if __name__ == "__main__":
    app = FileSelector()
    app.mainloop()
