# BotQueEscuchaStreamings


# Proyecto de Transcripción Automática de Audio con Whisper y CUDA

Este proyecto permite la transcripción automática de audio en tiempo real utilizando el modelo de Whisper, aprovechando los núcleos CUDA de la tarjeta gráfica para acelerar el proceso. A continuación, se detallan los pasos y configuraciones necesarios para poner en marcha el proyecto.

## Requisitos

- Anaconda con Jupyter Notebook instalado.
- Una tarjeta gráfica con soporte para CUDA.
- Dependencias de Python:
  - `torch`
  - `whisper`
  - `pydub`
  - `ffmpeg`
  - `wave`
  - `contextlib`
  - `subprocess`
  - `datetime`
  - `threading`
  - `shutil`

## Instalación de Dependencias

Para instalar las dependencias necesarias, se recomienda utilizar Anaconda para crear un entorno virtual:

```bash
conda create -n whisper_env python=3.8
conda activate whisper_env
pip install torch whisper pydub ffmpeg-python
