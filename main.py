import os
import time
import subprocess
import whisper
import torch
import threading

# Verificar si CUDA está disponible y usarlo si es posible
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Cargar el modelo más potente de Whisper
model = whisper.load_model("large-v2").to(device)

# Ruta al archivo MP3
audio_file = "output.mp3"

# Comando de ffmpeg para capturar el audio
ffmpeg_command = [
    "ffmpeg",
    "-f", "dshow",
    "-i", "audio=Mezcla estéreo (Realtek(R) Audio)",
    "-acodec", "libmp3lame",
    "-ab", "128k",
    "-ac", "2",
    "-y", audio_file
]

# Función para transcribir el audio desde un archivo
def transcribe_audio_segment(file, start_time, end_time):
    try:
        # Cortar el segmento de audio
        segment_file = "segment.mp3"
        cut_command = [
            "ffmpeg",
            "-i", file,
            "-ss", str(start_time),
            "-to", str(end_time),
            "-c", "copy",
            segment_file,
            "-y"
        ]
        subprocess.run(cut_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        
        # Transcribir el segmento de audio
        result = model.transcribe(segment_file)
        return result["text"]
    except Exception as e:
        print(f"Error transcribing audio segment: {e}")
        return ""

# Función para monitorear y transcribir el audio en tiempo real
def monitor_and_transcribe(file):
    while not os.path.exists(file):
        print(f"Waiting for {file} to be created...")
        time.sleep(0.1)

    print(f"{file} has been created. Starting transcription...")
    last_modification_time = os.path.getmtime(file)
    start_time = 0
    segment_duration = 5  # Duración del segmento en segundos

    while True:
        current_modification_time = os.path.getmtime(file)
        if current_modification_time != last_modification_time:
            last_modification_time = current_modification_time
            end_time = start_time + segment_duration  # Transcribir los últimos 5 segundos
            text = transcribe_audio_segment(file, start_time, end_time)
            start_time = end_time  # Actualizar el tiempo de inicio para el próximo segmento
            if text:
                print(f"Transcription: {text}")

        time.sleep(0.1)  # Verificar actualizaciones cada 0.1 segundos

# Función para ejecutar ffmpeg en un hilo separado
def run_ffmpeg():
    subprocess.run(ffmpeg_command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

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
