import os
import time
import subprocess
import whisper
import torch
import threading

# Configurar la variable de entorno para evitar la fragmentación de la memoria CUDA
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

# Verificar si CUDA está disponible y usarlo si es posible
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Cargar el modelo de Whisper con el idioma español
model = whisper.load_model("small", device=device)

# Ruta al archivo WAV
audio_file = "pruebavocesdosmedicionesbuena.wav"

# Comando de ffmpeg para capturar el audio solo de voces
ffmpeg_command = [
    "ffmpeg",
    "-f", "dshow",
    "-i", "audio=Mezcla estéreo (Realtek(R) Audio)",
    "-acodec", "pcm_s16le",  # WAV format
    "-ar", "44100",  # Frecuencia de muestreo
    "-ac", "1",  # Estéreo
    "-af", "highpass=f=200, lowpass=f=3000",  # Filtros de paso alto y bajo para aislar voces
    "-y", audio_file
]

print("Comando de ffmpeg configurado correctamente")

# Función para transcribir el audio completo al español y medir el tiempo de transcripción
def transcribe_audio(file, start_minute):
    print("Starting transcription...")
    try:
        start_time = time.time()  # Tiempo de inicio
        result = model.transcribe(file, language='es')  # Transcribir al español
        end_time = time.time()  # Tiempo de finalización
        transcription_time = end_time - start_time  # Calcular el tiempo de transcripción
        print(f"Transcription complete in {transcription_time:.2f} seconds at minute {start_minute:.2f}.")
        return result["text"], transcription_time
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return "", 0

# Función para monitorear y transcribir el audio en tiempo real
def monitor_and_transcribe(file):
    while not os.path.exists(file):
        print(f"Waiting for {file} to be created...")
        time.sleep(0.1)

    # Agregar una pausa inicial para asegurarse de que el archivo de audio se haya creado correctamente
    time.sleep(5)

    print(f"{file} has been created. Starting transcription...")
    last_modification_time = os.path.getmtime(file)
    total_transcription_time = 0
    segment_duration = 5  # Duración del segmento en segundos; ajustar según la capacidad de la GPU
    start_minute = 0

    while True:
        current_modification_time = os.path.getmtime(file)
        if current_modification_time != last_modification_time:
            last_modification_time = current_modification_time
            start_minute = (current_modification_time - os.path.getctime(file)) / 60  # Calcular minuto de inicio de transcripción
            text, transcription_time = transcribe_audio(file, start_minute)
            total_transcription_time += transcription_time
            if text:
                print(f"Transcription: {text}")

        time.sleep(segment_duration / 2)  # Verificar actualizaciones cada 0.1 segundos

    # print(f"Total transcription time: {total_transcription_time:.2f} seconds.")

# Función para ejecutar ffmpeg en un hilo separado
def run_ffmpeg():
    print("Starting FFmpeg...")
    subprocess.run(ffmpeg_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    print("FFmpeg has stopped.")

if __name__ == "__main__":
    # Crear y iniciar el hilo para ffmpeg
    ffmpeg_thread = threading.Thread(target=run_ffmpeg)
    ffmpeg_thread.start()

    try:
        # Monitorear y transcribir el archivo de audio
        monitor_and_transcribe(audio_file)
    finally:
        # Asegurarse de terminar el proceso de ffmpeg al finalizar
        ffmpeg_thread.join()
        print("FFmpeg thread has finished.")
