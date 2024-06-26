import os
import time
import whisper
import torch
import subprocess
import threading
import datetime
import shutil
import wave
import contextlib
import pydub
from pydub import AudioSegment

'''
Este va a ser el paso 1 , que va a consistir en lo siguiente 
    - Inicializamos una variable de entorno para configurar el tema de la grafica y los nucleos CUDA
    - Detectamos con la libreria de torch de Python , para ver si tienes nucleos CUDA 
    - Una vez detectado nucleos CUDA , cargamos el modelo y se lo asignamos a la grafica
    - Generamos la ruta del fichero original y el de copia que es el nombre .wav
    - Una vez cargado el modelo en la grafica tenemos que crear , el comando de ffmeg
    - Variable que guarda el tiempo de la grabación del audio original en formato .wav
    - funcion para ejecutarlo y y que se grabe bien 
'''

# Configurar la variable de entorno para evitar la fragmentación de la memoria CUDA
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

# Verificar si CUDA está disponible y usarlo si es posible
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Cargar el modelo de Whisper con el idioma español
model = whisper.load_model("small", device=device)

# Ruta al archivo WAV del audio que se va a grabar de forma continua 
audio_file = "pruebadepuradalocamente.wav"

# Creamos un array con todas las transcripciones 
all_transcriptions = dict()

# Tiempo que tienen que durar los segmentos 
segments_time = 60

# Archivo que sirve para hacer la copia del archivo de Audio original y hacerlo segmentos 
snapshot_file = "snapshot.wav"

# Establecemos un formato para que todos los segmentos tengan la misma nomenclatura
segment_file_template = "segment_%03d.wav"

# Crearemos un diccionario que lo que guarde basicamente es el segmento con su identificador como clave y como valor tenga el tiempo que ha tardado
# En transcribirlo 
segments_and_time_to_transcription = dict()

# Comando de ffmpeg para capturar el audio solo de voces
ffmpeg_command = [
    "ffmpeg",
    "-f", "dshow",
    "-i", "audio=Mezcla estéreo (Realtek(R) Audio)",
    "-acodec", "pcm_s16le",  # WAV format
    "-ar", "44100",  # Frecuencia de muestreo
    "-ac", "1",  # Estéreo
    "-af", "highpass=f=200, lowpass=f=3000",  # Filtros de paso alto y bajo para aislar voces
    "-progress", "-",  # Muestra el progreso en la salida estándar
    "-y", audio_file
]

# Guardamos una variable a nivel global para medir el tiempo de la duración que lleva el archivo de audio original 
time_original_file = "00:00:00"

# Esta constante lo qye va a marcar es la duración de un segmento lo ponemos en el mismo formato que time_original_file para poder comparar el contenido
segment_to_compare_str = "00:02:00"

# Necesitamos crear una variable con un indice que lo que nos permita sea comprobar cuantos segmentos hemos hecho y de forma ordenada transcribir 
# Esos segmentos 
segment_index = 0

# Establecemos una vatiable que lo que vaya haciendo es guardar el tiempo de finalización de cada segmento escrito
start_time_for_each_segment = 0


# Variable global para empezar en ms 
start_ms = 0

# Variable global para finalizar en ms 
end_ms = 2 * 60 * 1000


# Función para convertir la duración de FFmpeg al formato deseado
def convert_duration(duration_str):
    try:
        duration = datetime.datetime.strptime(duration_str.split('.')[0], '%H:%M:%S')
        return duration.strftime('%H:%M:%S')
    except ValueError:
        return "00:00:00"

# Función para ejecutar ffmpeg en un hilo separado y nos encargamos también de capturar la duración del archivo original de audio constantemente
def run_ffmpeg():
    global time_original_file

    print("Starting FFmpeg...")
    process = subprocess.Popen(ffmpeg_command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True, text=True)
    
    start_time = time.time()
    last_print_time = start_time
    
    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            if "out_time=" in line:
                duration_str = line.split("out_time=")[-1].strip()
                time_original_file = convert_duration(duration_str)
                current_time = time.time()
                elapsed_time = current_time - start_time
                
                # Imprimir duración cada 60 segundos o 1 minuto que es el tiempo establecido para cada segmento 
                if current_time - last_print_time >= segments_time:
                    print(f"Current recording duration: {duration_str}")
                    print(f"Tiempo convertido que guardo como variable global : {time_original_file}")
                    last_print_time = current_time

    except Exception as e:
        print(f"Error during FFmpeg execution: {e}")

    finally:
        process.stdout.close()
        process.wait()

'''
    Paso 2
    - Tenemos que generar una copia del archivo original funcion ()
    - Ese archivo de copia tenemos que tener en cuenta sobretodo la finalizacion
    - Que tenga la longitud correcta de 1 minuto de duración
'''

'''
    Bien cada segmento de la copia del archivo del audio original que esta grabandose de forma continuada e ininterrupida 
    se guardara en un diccionario , antes de la eliminación de dicho segmento que tendta que tener este formato
    {
        "[00(horas incio):00(minutos inicio):00(segundos inicio) - 00(horas final):00(minutos final):00(segundos final)]" : "Transcripción texto dicho fragmento"
    }
'''

# Funcion para formatear la duración en horas minutos y segundos
def format_duration(duration):
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


# Esta funcion lo que define es la copia del archivo original que tiene un inicio y un final fijo 
def generate_copy_audio_file(file, copy_audio_file, start_ms, end_ms):
    audio = AudioSegment.from_wav(file)
    porcion_audio = audio[start_ms:end_ms]
    porcion_audio.export(copy_audio_file, format="wav")
    print("Copy of the original file successfuly")

# Esta función se encargara de trozear ese archivo que se ha copiado para dividirlo en segementos de 1 minuto para maximizar la velocidad
# de transcripción con Whisper
def get_copy_wav_duration(copy_file):
    with contextlib.closing(wave.open(copy_file, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
        return duration

'''
    Tenemos que probar en este punto que realizamos los procesos de manera simultanea es decir 
    que el archivo de audio original se siga generando y modificando constantemente en consecuencia con el paso del tiempo.
    Por otro lado simultaneamente tenemos que generar esta copia que cuya duración minima la tenemos que establecer de 1 minuto 
    porque es el tiempo establecido para nuestro segmentos que posteriormente se van a transcribir
'''

# Hacemos otra funcion que se ejecutara en otro hilo que se encargara de comprobar que el tiempo del archivo de audio original es igual o superior 
# a 60 segundos/ 1 minuto 

def check_time_orginal_file():
    global time_original_file
    global segment_to_compare_str
    time_segments = segment_to_compare_str
    total_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(time_original_file.split(":"))))
    segment_seconds = sum(int(x) * 60 ** i for i, x in enumerate(reversed(time_segments.split(":"))))
    return total_seconds % segment_seconds == 0

# Funcion que se encargara en trozear la copia del archivo de audio original en segmentos de 60 segundos/ 1 minuto 
def cut_in_segments():
    global segment_file_template
    global segments_time
    global snapshot_file
    ffmpeg_segment_command = [
        "ffmpeg",
        "-i", snapshot_file,
        "-f", "segment",
        "-segment_time", str(segments_time),
        "-c", "copy",
        segment_file_template
    ]
    print("Executed command for doing segments from the snapshot file")
    process = subprocess.Popen(ffmpeg_segment_command, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True, text=True)
    process.wait()
    print("Segments are created")


# Funcion que se va a encargar de acumular en la variable al duración de cada segmento para que la siguiente copia del archivo de audio original 
# Empieze por donde tenga que empezar y no repita 
def update_last_segment_start_time(file):
    global start_time_for_each_segment
    global segment_to_compare_str
    duration_segment = get_copy_wav_duration(file)
    start_time_for_each_segment += duration_segment
    segment_to_compare_str = format_duration(start_time_for_each_segment)



#Funcion para escribir las transcripciones en al archivo de texto
def write_transcriptions_to_file():
    global all_transcriptions
    with open("transcripciones.txt", "w", encoding="utf-8") as transcript_file:
        for time_range, text in all_transcriptions.items():
            transcript_file.write(f"{time_range}: {text}\n")


# Funcion que se tiene que encargar de eliminar cualquier archivo de audio en formato .WAV
def delete_audio_file(file):
    if os.path.exists(file):
        os.remove(file)
        time.sleep(2)
        print(f"Deleted file: {file}")
    else:
        print(f"File not found: {file}")
    

#Función cuyo proposito es transcribir un segmento de audio que le hemos porporcionado pero de manera individual
def transcribe_individual_segment(file):
    global segments_and_time_to_transcription
    global start_time_for_each_segment
    try:
        print(f"Entrando a transcribir cada segmento que hemos generado : {file}")
        start_transcription = time.time()
        result = model.transcribe(file, language='es')
        end_transcription = time.time()
        
        transcription_time = end_transcription - start_transcription
        print(f"Segment that was transcripted : segment_{file}")
        print(f"Transcription complete in {transcription_time:.2f} seconds.")
        segments_and_time_to_transcription[file] = format_duration(transcription_time)
        update_last_segment_start_time(file)
        print(f"The time updated for finish segment : {file} , and the time is : {start_time_for_each_segment}")
        return result["text"], transcription_time
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return "", 0



# Función que lo que va ha hacer es encargarse de transcribir cada segmento de forma ordenada
def transcribe_segments():
    global segment_file_template
    global segments_time
    global start_time_for_each_segment
    global segment_index
    global all_transcriptions
    for i in range(2):
        segment_file = segment_file_template % segment_index
        print(f"Lo que esta guardando segment_file : {segment_file}")
        if not os.path.exists(segment_file):
            print(f"Archivo no encontrado : {segment_file}")
            break
        text, transcription_time = transcribe_individual_segment(segment_file)
        print("Ya ha transcrito todos los segmentos correspondientes")
        end_time_segment_str_timestamp = format_duration(start_time_for_each_segment + segments_time)
        time_to_save = f"[{start_time_for_each_segment} - {end_time_segment_str_timestamp}]"
        all_transcriptions[time_to_save] = text
        print("Lo guardamso en el archivo de texto la transcripcion ")
        write_transcriptions_to_file()
        print("Eliminamos este segmento")
        delete_audio_file(segment_file)
        segment_index += 1
    segment_index = 0


# Punto de entrada del código 
if __name__ == "__main__":

    global snapshot_file
    global audio_file
    global start_ms 
    global end_ms
    global segment_index
    global segment_to_compare_str

    #Creamos el archivo de texto que lo que va a guardar son las transcripciones 
    with open("transcripciones.txt", "w", encoding="utf-8") as transcript_file:
        transcript_file.write("")
        
    
    # Crear y iniciar el hilo para ffmpeg
    ffmpeg_thread = threading.Thread(target=run_ffmpeg)
    ffmpeg_thread.start()

    print(f"Waiting for {audio_file} to be created...")
    time.sleep(0.1)

    # Agregar una pausa inicial para asegurarse de que el archivo de audio se haya creado correctamente
    time.sleep(5)
    print("FFmpeg thread is running. Recording audio...")

    # Mantener el programa principal corriendo para permitir la grabación continua
    try:
        while True:
            if check_time_orginal_file():
                generate_copy_audio_file(audio_file, snapshot_file, start_ms, end_ms)
                cut_in_segments()
                transcribe_segments()
                #Reseteamos a 0 el contador de segmentos 
                segment_index = 0
                delete_audio_file(snapshot_file)
                # Actualizar para la proxima
                start_ms = end_ms
                end_ms += 2 * 60 * 1000
                segment_to_compare_str = format_duration(end_ms / 1000)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping recording.")
        ffmpeg_thread.join()
        print("FFmpeg thread has finished.")    
