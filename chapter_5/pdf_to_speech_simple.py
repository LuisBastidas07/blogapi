import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# Comprueba si podemos importar las bibliotecas requeridas
try:
    import PyPDF2
    import pyttsx3
    HAS_LIBRARIES = True
except ImportError:
    HAS_LIBRARIES = False

def instalar_requisitos():
    """Instala las bibliotecas necesarias"""
    print("Instalando requisitos necesarios...")
    os.system("pip install PyPDF2 pyttsx3")
    print("Instalación completada. Por favor, reinicia el programa.")
    input("Presiona Enter para salir...")
    sys.exit()

class PDFToSpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF a Audio - Conversor")
        self.root.geometry("500x400")
        
        # Variables
        self.pdf_path = ""
        self.extracted_text = ""
        self.engine = pyttsx3.init()
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
        
        self.speed_scale = ttk.Scale(speed_frame, from_=50, to=300, orient=tk.HORIZONTAL)
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
        
        self.voice_combobox = ttk.Combobox(voice_frame, values=voice_options, state="readonly")
        self.voice_combobox.current(0)  # Seleccionar la primera voz
        self.voice_combobox.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.voice_combobox.bind("<<ComboboxSelected>>", self.change_voice)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.process_button = ttk.Button(button_frame, text="Procesar PDF", command=self.process_pdf)
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        self.play_button = ttk.Button(button_frame, text="Reproducir", command=self.play_audio, state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        # Área de texto para mostrar el contenido del PDF
        text_frame = ttk.LabelFrame(main_frame, text="Texto extraído", padding="10")
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
    
    def process_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un archivo PDF primero")
            return
        
        try:
            self.status_label.config(text="Procesando PDF...")
            self.root.update_idletasks()
            
            # Extraer texto
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page_num in range(len(reader.pages)):
                    text += reader.pages[page_num].extract_text() + "\n"
            
            if not text.strip():
                messagebox.showinfo("Información", "No se pudo extraer texto del PDF. Podría ser un PDF escaneado que necesita OCR.")
                self.status_label.config(text="PDF sin texto extraíble")
                return
            
            self.extracted_text = text
            self.text_preview.delete(1.0, tk.END)
            self.text_preview.insert(tk.END, text[:500] + "..." if len(text) > 500 else text)
            
            self.play_button.config(state=tk.NORMAL)
            self.status_label.config(text="PDF procesado correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar el PDF: {str(e)}")
            self.status_label.config(text="Error al procesar PDF")
    
    def play_audio(self):
        if not self.extracted_text:
            messagebox.showwarning("Advertencia", "No hay texto para reproducir")
            return
        
        try:
            # Configurar velocidad
            rate = int(self.speed_scale.get())
            self.engine.setProperty('rate', rate)
            
            # Reproducir
            self.status_label.config(text="Reproduciendo audio...")
            self.play_button.config(state=tk.DISABLED)
            self.root.update_idletasks()
            
            self.engine.say(self.extracted_text)
            self.engine.runAndWait()
            
            self.play_button.config(state=tk.NORMAL)
            self.status_label.config(text="Reproducción finalizada")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al reproducir: {str(e)}")
            self.status_label.config(text="Error en la reproducción")
            self.play_button.config(state=tk.NORMAL)

if __name__ == "__main__":
    # Verificar si tenemos las bibliotecas necesarias
    if not HAS_LIBRARIES:
        root = tk.Tk()
        root.withdraw()  # Ocultar ventana principal
        respuesta = messagebox.askyesno(
            "Bibliotecas faltantes", 
            "Se necesitan instalar algunas bibliotecas para ejecutar este programa.\n\n¿Desea instalarlas ahora?"
        )
        if respuesta:
            instalar_requisitos()
        else:
            sys.exit()
    
    # Iniciar la aplicación
    root = tk.Tk()
    app = PDFToSpeechApp(root)
    root.mainloop()
