import os
import rawpy
import threading
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox
from concurrent.futures import ThreadPoolExecutor

class NefConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Pro RAW to JPEG Converter")
        self.geometry("550x450")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.selected_paths = []

        # UI Layout
        self.label = ctk.CTkLabel(self, text="NEF to JPG Converter", font=("Arial", 26, "bold"))
        self.label.pack(pady=(30, 10))

        self.btn_files = ctk.CTkButton(self, text="Select Individual Files", command=self.select_files)
        self.btn_files.pack(pady=10)

        self.btn_folder = ctk.CTkButton(self, text="Select Entire Folder", command=self.select_folder)
        self.btn_folder.pack(pady=10)

        # Progress Section
        self.status_label = ctk.CTkLabel(self, text="No files selected", text_color="gray")
        self.status_label.pack(pady=(20, 5))

        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.set(0) # Start at 0%
        self.progress_bar.pack(pady=10)

        self.convert_btn = ctk.CTkButton(
            self, text="Start Batch Conversion", 
            fg_color="#2ecc71", hover_color="#27ae60", 
            command=self.start_conversion_thread
        )
        self.convert_btn.pack(pady=30)

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("NEF files", "*.NEF"), ("All files", "*.*")])
        if files:
            self.selected_paths = list(files)
            self.status_label.configure(text=f"{len(self.selected_paths)} files selected", text_color="white")
            self.progress_bar.set(0)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_paths = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.nef')]
            self.status_label.configure(text=f"Found {len(self.selected_paths)} NEF files", text_color="white")
            self.progress_bar.set(0)

    def convert_nef_to_jpg(self, nef_path):
        try:
            with rawpy.imread(nef_path) as raw:
                # Process RAW to RGB
                rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=False, bright=1.0)
                
                # Create output path
                target_path = os.path.splitext(nef_path)[0] + ".jpg"
                
                # Save via Pillow
                image = Image.fromarray(rgb)
                image.save(target_path, "JPEG", quality=95)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def start_conversion_thread(self):
        if not self.selected_paths:
            messagebox.showwarning("Warning", "Please select files first!")
            return

        # Disable UI elements during work
        self.convert_btn.configure(state="disabled")
        self.btn_files.configure(state="disabled")
        self.btn_folder.configure(state="disabled")
        
        # Launch manager thread
        threading.Thread(target=self.run_batch_logic, daemon=True).start()

    def run_batch_logic(self):
        total = len(self.selected_paths)
        completed = 0
        success_count = 0

        # max_workers=5 limits concurrency to 5 images at a time
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Map the file list to the worker function
            future_to_path = {executor.submit(self.convert_nef_to_jpg, path): path for path in self.selected_paths}
            
            for future in future_to_path:
                if future.result():
                    success_count += 1
                
                completed += 1
                # Calculate progress (0.0 to 1.0)
                progress = completed / total
                
                # Update UI safely from thread
                self.after(0, lambda p=progress, c=completed, t=total: self.update_progress_ui(p, c, t))

        # Final cleanup on Main Thread
        self.after(0, lambda: self.finalize_conversion(success_count))

    def update_progress_ui(self, progress, current, total):
        self.progress_bar.set(progress)
        self.status_label.configure(text=f"Processing {current} of {total}...")

    def finalize_conversion(self, count):
        self.convert_btn.configure(state="normal")
        self.btn_files.configure(state="normal")
        self.btn_folder.configure(state="normal")
        self.status_label.configure(text="Conversion Complete!", text_color="#2ecc71")
        messagebox.showinfo("Done", f"Successfully converted {count} files!")

if __name__ == "__main__":
    app = NefConverterApp()
    app.mainloop()
