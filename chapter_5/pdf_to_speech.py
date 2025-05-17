import sys
import os
import threading
import PyPDF2
import pyttsx3
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import pytesseract
from pdf2image import convert_from_path
import tempfile

class PDFToSpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF a Audio - Conversor")
        self.root.geometry("600x450")
        self.root.resizable(True, True)
        
        # Variables
        self.pdf_path = ""
        self.output_audio_path = ""
        self.extracted_text = ""
        self.is_processing = False
        self.engine = pyttsx3.init()
        self.current_voice_index = 0
        self.available_voices = self.engine.getProperty('voices')
        
        # Crear interfaz
        self.create_widgets()
        
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="Conversor de PDF a Audio", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)
        
        # Frame para selección de archivo
        file_frame = ttk.LabelFrame(main_frame, text="Selección de Archivo", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_path_entry = ttk.Entry(file_frame, width=50)
        self.file_path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(file_frame, text="Examinar", command=self.browse_file)
        browse_button.pack(side=tk.RIGHT, padx=5)
        
        # Frame para configuraciones
        config_frame = ttk.LabelFrame(main_frame, text="Configuraciones", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        
        # Control de velocidad
        speed_frame = ttk.Frame(config_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        
        speed_label = ttk.Label(speed_frame, text="Velocidad:")
        speed_label.pack(side=tk.LEFT, padx=5)
        
        self.speed_scale = ttk.Scale(speed_frame, from_=50, to=300, orient=tk.HORIZONTAL, length=200)
        self.speed_scale.set(150)  # Valor predeterminado
        self.speed_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        self.speed_value_label = ttk.Label(speed_frame, text="150%")
        self.speed_value_label.pack(side=tk.LEFT, padx=5)
        
        self.speed_scale.config(command=self.update_speed_label)
        
        # Selección de voz
        voice_frame = ttk.Frame(config_frame)
        voice_frame.pack(fill=tk.X, pady=5)
        
        voice_label = ttk.Label(voice_frame, text="Voz:")
        voice_label.pack(side=tk.LEFT, padx=5)
        
        voice_options = []
        for voice in self.available_voices:
            name = voice.name
            if hasattr(voice, 'id'):
                lang = voice.id.split('\\')[-1] if '\\' in voice.id else voice.id
                name = f"{name} ({lang})"
            voice_options.append(name)
        
        if not voice_options:  # Si no hay voces disponibles
            voice_options = ["Voz predeterminada"]
        
        self.voice_combobox = ttk.Combobox(voice_frame, values=voice_options, state="readonly", width=40)
        self.voice_combobox.current(0)  # Seleccionar la primera voz
        self.voice_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.voice_combobox.bind("<<ComboboxSelected>>", self.change_voice)
        
        # Frame para opciones de salida
        output_frame = ttk.LabelFrame(main_frame, text="Opciones de Salida", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        # Checkbox para guardar archivo
        self.save_output = tk.BooleanVar(value=True)
        save_checkbox = ttk.Checkbutton(output_frame, text="Guardar como archivo de audio", variable=self.save_output)
        save_checkbox.pack(fill=tk.X, pady=5)
        
        # Frame para botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.process_button = ttk.Button(button_frame, text="Procesar PDF", command=self.process_pdf)
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        self.play_button = ttk.Button(button_frame, text="Reproducir", command=self.play_audio, state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = ttk.Button(button_frame, text="Guardar Audio", command=self.save_audio, state=tk.DISABLED)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=100, variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, pady=10)
        
        # Área de texto para mostrar el contenido del PDF
        text_frame = ttk.LabelFrame(main_frame, text="Vista previa del texto", padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.text_preview = tk.Text(text_frame, wrap=tk.WORD, height=8)
        self.text_preview.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(text_frame, command=self.text_preview.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.text_preview.config(yscrollcommand=scrollbar.set)
        
        # Etiqueta de estado
        self.status_label = ttk.Label(main_frame, text="Listo para procesar")
        self.status_label.pack(pady=5)
    
    def update_speed_label(self, event=None):
        value = int(self.speed_scale.get())
        self.speed_value_label.config(text=f"{value}%")
    
    def change_voice(self, event=None):
        selected_index = self.voice_combobox.current()
        if 0 <= selected_index < len(self.available_voices):
            self.engine.setProperty('voice', self.available_voices[selected_index].id)
            self.current_voice_index = selected_index
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo PDF",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.pdf_path = file_path
            self.file_path_entry.delete(0, tk.END)
            self.file_path_entry.insert(0, file_path)
            self.status_label.config(text=f"Archivo seleccionado: {os.path.basename(file_path)}")
    
    def extract_text_from_pdf(self, pdf_path):
        text = ""
        try:
            # Intenta extraer texto directamente del PDF
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                
                for i in range(num_pages):
                    self.progress_var.set((i / num_pages) * 100)
                    self.root.update_idletasks()
                    
                    page = reader.pages[i]
                    page_text = page.extract_text()
                    
                    # Si la página no tiene texto, intenta OCR
                    if not page_text or page_text.isspace():
                        # Convierte la página del PDF a imagen
                        self.status_label.config(text=f"Aplicando OCR a la página {i+1}/{num_pages}...")
                        with tempfile.TemporaryDirectory() as temp_dir:
                            images = convert_from_path(pdf_path, first_page=i+1, last_page=i+1)
                            for image in images:
                                # Realizar OCR en la imagen
                                page_text = pytesseract.image_to_string(image)
                    
                    text += f"\n--- Página {i+1} ---\n{page_text}\n"
            
            # Si después de intentar todo el documento no hay texto, aplicar OCR al documento completo
            if not text.strip():
                self.status_label.config(text="El PDF no contiene texto. Aplicando OCR a todo el documento...")
                with tempfile.TemporaryDirectory() as temp_dir:
                    images = convert_from_path(pdf_path)
                    for i, image in enumerate(images):
                        self.progress_var.set((i / len(images)) * 100)
                        self.root.update_idletasks()
                        page_text = pytesseract.image_to_string(image)
                        text += f"\n--- Página {i+1} ---\n{page_text}\n"
        
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar el PDF: {str(e)}")
            return ""
        
        return text
    
    def process_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un archivo PDF primero.")
            return
        
        if self.is_processing:
            return
        
        self.is_processing = True
        self.process_button.config(state=tk.DISABLED)
        self.play_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.text_preview.delete(1.0, tk.END)
        self.status_label.config(text="Procesando PDF...")
        
        # Usar un hilo para no bloquear la interfaz
        threading.Thread(target=self._process_pdf_thread, daemon=True).start()
    
    def _process_pdf_thread(self):
        try:
            self.extracted_text = self.extract_text_from_pdf(self.pdf_path)
            
            # Actualizar la interfaz desde el hilo principal
            self.root.after(0, self._update_ui_after_processing)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error al procesar: {str(e)}"))
            self.root.after(0, self._reset_processing_state)
    
    def _update_ui_after_processing(self):
        if self.extracted_text:
            # Mostrar vista previa del texto (limitado a los primeros 1000 caracteres)
            preview_text = self.extracted_text[:3000] + "..." if len(self.extracted_text) > 3000 else self.extracted_text
            self.text_preview.delete(1.0, tk.END)
            self.text_preview.insert(tk.END, preview_text)
            
            self.play_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)
            self.status_label.config(text=f"PDF procesado. {len(self.extracted_text)} caracteres extraídos.")
        else:
            self.status_label.config(text="No se pudo extraer texto del PDF.")
        
        self._reset_processing_state()
    
    def _reset_processing_state(self):
        self.is_processing = False
        self.process_button.config(state=tk.NORMAL)
        self.progress_var.set(0)
    
    def play_audio(self):
        if not self.extracted_text:
            messagebox.showwarning("Advertencia", "No hay texto para reproducir.")
            return
        
        # Configurar la velocidad
        rate = int(self.speed_scale.get())
        self.engine.setProperty('rate', rate)
        
        # Reproducir
        self.status_label.config(text="Reproduciendo audio...")
        
        # Usar un hilo para reproducir el audio
        threading.Thread(target=self._play_audio_thread, daemon=True).start()
    
    def _play_audio_thread(self):
        try:
            self.engine.say(self.extracted_text)
            self.engine.runAndWait()
            self.root.after(0, lambda: self.status_label.config(text="Reproducción finalizada."))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error al reproducir: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="Error en la reproducción."))
    
    def save_audio(self):
        if not self.extracted_text:
            messagebox.showwarning("Advertencia", "No hay texto para guardar como audio.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Guardar archivo de audio",
            filetypes=[("Archivos MP3", "*.mp3"), ("Archivos WAV", "*.wav")],
            defaultextension=".mp3"
        )
        
        if not file_path:
            return
        
        self.status_label.config(text="Guardando archivo de audio...")
        self.save_button.config(state=tk.DISABLED)
        self.play_button.config(state=tk.DISABLED)
        
        # Usar un hilo para guardar el audio
        threading.Thread(target=self._save_audio_thread, args=(file_path,), daemon=True).start()
    
    def _save_audio_thread(self, file_path):
        try:
            # Configurar la velocidad
            rate = int(self.speed_scale.get())
            self.engine.setProperty('rate', rate)
            
            # Guardar como archivo
            self.engine.save_to_file(self.extracted_text, file_path)
            self.engine.runAndWait()
            
            self.root.after(0, lambda: self.status_label.config(text=f"Audio guardado en: {os.path.basename(file_path)}"))
            self.root.after(0, lambda: self.save_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.play_button.config(state=tk.NORMAL))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error al guardar el audio: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="Error al guardar el audio."))
            self.root.after(0, lambda: self.save_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.play_button.config(state=tk.NORMAL))

if __name__ == "__main__":
    # Verifica requisitos
    requirements_met = True
    
    try:
        import PyPDF2
    except ImportError:
        print("Instalando PyPDF2...")
        os.system("pip install PyPDF2")
    
    try:
        import pyttsx3
    except ImportError:
        print("Instalando pyttsx3...")
        os.system("pip install pyttsx3")
    
    try:
        import pytesseract
        import pdf2image
    except ImportError:
        print("Instalando pytesseract y pdf2image...")
        os.system("pip install pytesseract pdf2image")
        requirements_met = False
        print("NOTA: También necesitarás instalar Tesseract OCR en tu sistema:")
        print("- Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("- Mac: brew install tesseract")
        print("- Linux: sudo apt-get install tesseract-ocr")
    
    # Inicia la aplicación
    root = tk.Tk()
    app = PDFToSpeechApp(root)
    root.mainloop()
