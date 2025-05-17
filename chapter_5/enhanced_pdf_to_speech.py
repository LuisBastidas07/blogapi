import os
import sys
import time
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from datetime import datetime
from ttkthemes import ThemedTk

# Comprueba si podemos importar las bibliotecas requeridas
try:
    import PyPDF2
    import pyttsx3
    import pygame
    from gtts import gTTS
    HAS_LIBRARIES = True
except ImportError:
    HAS_LIBRARIES = False

def instalar_requisitos():
    """Instala las bibliotecas necesarias"""
    print("Instalando requisitos necesarios...")
    os.system("pip install PyPDF2 pyttsx3 pygame gTTS ttkthemes")
    print("Instalación completada. Por favor, reinicia el programa.")
    input("Presiona Enter para salir...")
    sys.exit()

class PDFToSpeechApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF a Audio - Conversor")
        self.root.geometry("550x650")
        
        # Configurar el estilo
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 10))
        style.configure("TLabel", font=("Helvetica", 10))
        style.configure("Header.TLabel", font=("Helvetica", 16, "bold"))
        style.configure("Status.TLabel", font=("Helvetica", 9, "italic"))
        
        # Variables
        self.pdf_path = ""
        self.extracted_text = ""
        self.engine = pyttsx3.init()
        self.available_voices = self.engine.getProperty('voices')
        self.pages_content = []  # Para almacenar el texto de cada página
        self.current_page = 0
        self.is_playing = False
        self.is_paused = False
        self.playback_thread = None
        self.temp_audio_file = None
        
        # Inicializar pygame para reproducción
        pygame.mixer.init()
        
        # Crear interfaz
        self.create_widgets()
    
    def create_widgets(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título y autor
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=5)
        
        title_label = ttk.Label(title_frame, text="Conversor de PDF a Audio", style="Header.TLabel")
        title_label.pack(side=tk.LEFT, pady=10)
        
        author_label = ttk.Label(title_frame, text="Created by: Luis Bastidas", font=("Helvetica", 8, "italic"))
        author_label.pack(side=tk.RIGHT, pady=10)
        
        # Frame para selección de archivo
        file_frame = ttk.LabelFrame(main_frame, text="Selección de Archivo", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_path_entry = ttk.Entry(file_frame, width=50)
        self.file_path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(file_frame, text="Examinar", command=self.browse_file)
        browse_button.pack(side=tk.RIGHT, padx=5)
        
        # Frame para selección de página
        page_frame = ttk.LabelFrame(main_frame, text="Selección de Página", padding="10")
        page_frame.pack(fill=tk.X, pady=5)
        
        page_label = ttk.Label(page_frame, text="Página:")
        page_label.pack(side=tk.LEFT, padx=5)
        
        self.page_var = tk.StringVar(value="1")
        self.page_spinbox = ttk.Spinbox(page_frame, from_=1, to=1, textvariable=self.page_var, width=5)
        self.page_spinbox.pack(side=tk.LEFT, padx=5)
        self.page_spinbox.bind("<<Increment>>", self.update_page_preview)
        self.page_spinbox.bind("<<Decrement>>", self.update_page_preview)
        self.page_spinbox.bind("<Return>", self.update_page_preview)
        self.page_spinbox.bind("<FocusOut>", self.update_page_preview)
        
        self.page_total_label = ttk.Label(page_frame, text="de 1")
        self.page_total_label.pack(side=tk.LEFT, padx=5)
        
        read_from_page_button = ttk.Button(page_frame, text="Leer desde esta página", command=self.set_reading_start_page)
        read_from_page_button.pack(side=tk.RIGHT, padx=5)
        
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
        
        # Botones de Procesamiento
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.process_button = ttk.Button(button_frame, text="Procesar PDF", command=self.process_pdf)
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        export_button = ttk.Button(button_frame, text="Exportar Audio", command=self.export_audio, state=tk.DISABLED)
        export_button.pack(side=tk.RIGHT, padx=5)
        self.export_button = export_button
        
        # Área de texto para mostrar el contenido del PDF
        text_frame = ttk.LabelFrame(main_frame, text="Vista previa del texto", padding="10")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.text_preview = tk.Text(text_frame, wrap=tk.WORD, height=8)
        self.text_preview.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(text_frame, command=self.text_preview.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        self.text_preview.config(yscrollcommand=scrollbar.set)
        
        # Controles de reproducción
        playback_frame = ttk.LabelFrame(main_frame, text="Controles de Reproducción", padding="10")
        playback_frame.pack(fill=tk.X, pady=5)
        
        # Botones de control
        control_frame = ttk.Frame(playback_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        rewind_button = ttk.Button(control_frame, text="⏪ -10s", command=self.rewind_audio, state=tk.DISABLED)
        rewind_button.pack(side=tk.LEFT, padx=5)
        self.rewind_button = rewind_button
        
        self.play_button = ttk.Button(control_frame, text="▶ Reproducir", command=self.play_audio, state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = ttk.Button(control_frame, text="⏸ Pausar", command=self.pause_audio, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="⏹ Detener", command=self.stop_audio, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        forward_button = ttk.Button(control_frame, text="⏩ +10s", command=self.forward_audio, state=tk.DISABLED)
        forward_button.pack(side=tk.LEFT, padx=5)
        self.forward_button = forward_button
        
        # Barra de progreso
        progress_frame = ttk.Frame(playback_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=100, mode='determinate', variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, padx=5, expand=True)
        
        # Etiqueta de tiempo
        self.time_label = ttk.Label(progress_frame, text="00:00 / 00:00")
        self.time_label.pack(pady=5)
        
        # Etiqueta de estado
        self.status_label = ttk.Label(main_frame, text="Listo para procesar", style="Status.TLabel")
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
                self.pages_content = []
                full_text = ""
                
                for page_num in range(len(reader.pages)):
                    page_text = reader.pages[page_num].extract_text() + "\n"
                    self.pages_content.append(page_text)
                    full_text += page_text
            
            if not full_text.strip():
                messagebox.showinfo("Información", "No se pudo extraer texto del PDF. Podría ser un PDF escaneado que necesita OCR.")
                self.status_label.config(text="PDF sin texto extraíble")
                return
            
            self.extracted_text = full_text
            
            # Actualizar la interfaz
            self.page_spinbox.config(from_=1, to=len(self.pages_content))
            self.page_total_label.config(text=f"de {len(self.pages_content)}")
            self.current_page = 0
            self.page_var.set("1")
            self.update_page_preview()
            
            # Habilitar botones
            self.play_button.config(state=tk.NORMAL)
            self.export_button.config(state=tk.NORMAL)
            self.status_label.config(text="PDF procesado correctamente")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar el PDF: {str(e)}")
            self.status_label.config(text="Error al procesar PDF")
    
    def update_page_preview(self, event=None):
        try:
            page_num = int(self.page_var.get()) - 1
            if 0 <= page_num < len(self.pages_content):
                self.current_page = page_num
                self.text_preview.delete(1.0, tk.END)
                self.text_preview.insert(tk.END, self.pages_content[page_num])
        except ValueError:
            pass  # Si el valor no es un número
    
    def set_reading_start_page(self):
        if not self.pages_content:
            messagebox.showinfo("Información", "Primero debe procesar un PDF")
            return
        
        try:
            page_num = int(self.page_var.get()) - 1
            if 0 <= page_num < len(self.pages_content):
                self.current_page = page_num
                messagebox.showinfo("Información", f"La lectura comenzará desde la página {page_num + 1}")
        except ValueError:
            messagebox.showwarning("Advertencia", "Número de página inválido")
    
    def play_audio(self):
        if not self.extracted_text:
            messagebox.showwarning("Advertencia", "No hay texto para reproducir")
            return
        
        if self.is_paused:
            # Continuar reproducción
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.status_label.config(text="Reproduciendo audio...")
            return
        
        if self.is_playing:
            return  # Ya se está reproduciendo
        
        try:
            # Crear texto a reproducir desde la página actual
            text_to_read = ""
            for i in range(self.current_page, len(self.pages_content)):
                text_to_read += self.pages_content[i]
            
            if not text_to_read.strip():
                messagebox.showinfo("Información", "No hay texto para reproducir en esta página")
                return
            
            # Configurar velocidad
            rate = int(self.speed_scale.get())
            self.engine.setProperty('rate', rate)
            
            # Crear un archivo temporal para la reproducción
            temp_dir = os.path.join(os.path.expanduser("~"), ".pdf_to_speech_temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            self.temp_audio_file = os.path.join(temp_dir, f"temp_audio_{int(time.time())}.mp3")
            
            # Iniciar hilo de reproducción
            self.playback_thread = threading.Thread(target=self.threaded_playback, args=(text_to_read,))
            self.playback_thread.daemon = True
            self.playback_thread.start()
            
            # Actualizar la interfaz
            self.is_playing = True
            self.play_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.NORMAL)
            self.rewind_button.config(state=tk.NORMAL)
            self.forward_button.config(state=tk.NORMAL)
            self.status_label.config(text="Preparando reproducción...")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al reproducir: {str(e)}")
            self.status_label.config(text="Error en la reproducción")
    
    def threaded_playback(self, text):
        try:
            # Generar archivo de audio con gTTS
            self.status_label.config(text="Generando audio...")
            self.root.update_idletasks()
            
            tts = gTTS(text=text, lang='es')
            tts.save(self.temp_audio_file)
            
            # Reproducir con pygame
            pygame.mixer.music.load(self.temp_audio_file)
            pygame.mixer.music.play()
            
            # Obtener duración
            sound = pygame.mixer.Sound(self.temp_audio_file)
            duration = sound.get_length()
            
            # Actualizar la interfaz
            self.status_label.config(text="Reproduciendo audio...")
            self.root.update_idletasks()
            
            # Actualizar barra de progreso
            start_time = time.time()
            while pygame.mixer.music.get_busy() and self.is_playing:
                if not self.is_paused:
                    elapsed = time.time() - start_time
                    progress = min(100, (elapsed / duration) * 100)
                    
                    # Formatear tiempo
                    elapsed_min = int(elapsed) // 60
                    elapsed_sec = int(elapsed) % 60
                    total_min = int(duration) // 60
                    total_sec = int(duration) % 60
                    
                    self.progress_var.set(progress)
                    self.time_label.config(text=f"{elapsed_min:02d}:{elapsed_sec:02d} / {total_min:02d}:{total_sec:02d}")
                
                time.sleep(0.1)
                self.root.update_idletasks()
            
            # Restablecer la interfaz cuando termina
            if not self.is_paused and self.is_playing:
                self.stop_audio()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error en la reproducción: {str(e)}")
            self.stop_audio()
    
    def pause_audio(self):
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.status_label.config(text="Reproducción pausada")
            self.play_button.config(state=tk.NORMAL)
    
    def stop_audio(self):
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            
            # Restablecer interfaz
            self.progress_var.set(0)
            self.time_label.config(text="00:00 / 00:00")
            self.play_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
            self.rewind_button.config(state=tk.DISABLED)
            self.forward_button.config(state=tk.DISABLED)
            self.status_label.config(text="Reproducción detenida")
            
            # Eliminar archivo temporal si existe
            if self.temp_audio_file and os.path.exists(self.temp_audio_file):
                try:
                    os.remove(self.temp_audio_file)
                except:
                    pass
    
    def rewind_audio(self):
        if self.is_playing:
            current_pos = pygame.mixer.music.get_pos() / 1000  # en segundos
            new_pos = max(0, current_pos - 10)
            pygame.mixer.music.play(start=new_pos)
    
    def forward_audio(self):
        if self.is_playing:
            current_pos = pygame.mixer.music.get_pos() / 1000  # en segundos
            new_pos = current_pos + 10
            pygame.mixer.music.play(start=new_pos)
    
    def export_audio(self):
        if not self.extracted_text:
            messagebox.showwarning("Advertencia", "No hay texto para exportar")
            return
        
        try:
            # Seleccionar dónde guardar
            save_path = filedialog.asksaveasfilename(
                title="Guardar audio como",
                defaultextension=".mp3",
                filetypes=[("Archivo MP3", "*.mp3"), ("Archivo WAV", "*.wav")]
            )
            
            if not save_path:
                return
            
            # Crear texto a exportar desde la página actual
            text_to_export = ""
            export_from_page = messagebox.askyesno(
                "Exportar audio", 
                f"¿Desea exportar desde la página {self.current_page + 1} hasta el final?\n\n"
                "Seleccione 'No' para exportar todo el documento."
            )
            
            if export_from_page:
                for i in range(self.current_page, len(self.pages_content)):
                    text_to_export += self.pages_content[i]
            else:
                text_to_export = self.extracted_text
            
            # Mostrar progreso
            self.status_label.config(text="Generando archivo de audio...")
            self.root.update_idletasks()
            
            # Generar archivo de audio
            tts = gTTS(text=text_to_export, lang='es')
            tts.save(save_path)
            
            # Confirmar
            self.status_label.config(text=f"Audio guardado en: {os.path.basename(save_path)}")
            messagebox.showinfo("Éxito", f"El archivo de audio se ha guardado correctamente en:\n{save_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar el audio: {str(e)}")
            self.status_label.config(text="Error al exportar audio")

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
    
    # Iniciar la aplicación con tema
    try:
        root = ThemedTk(theme="arc")  # Usar un tema más moderno
    except:
        root = tk.Tk()  # Si falla, usar el tema predeterminado
    
    app = PDFToSpeechApp(root)
    root.mainloop()
