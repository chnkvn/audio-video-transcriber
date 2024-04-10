FROM python:3.11-bullseye as builder

RUN apt-get -y update && apt-get -y upgrade && apt-get -y install git git-lfs wget ffmpeg
WORKDIR /usr/src/app
RUN python -m pip install --upgrade pip setuptools wheel
COPY . .
RUN pip install -r requirements.txt
RUN pip install gradio
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='bofenghuang/whisper-large-v3-french-distil-dec16', local_dir='./models/whisper-large-v3-french-distil-dec16', allow_patterns='ctranslate2/*')"
WORKDIR /usr/src/app/models
RUN git clone https://huggingface.co/Systran/faster-whisper-large-v2
RUN git clone https://huggingface.co/Systran/faster-distil-whisper-large-v2
WORKDIR /usr/src/app/whisper_cpu/
#ENV PYTHONPATH .
FROM builder as python_done
EXPOSE 7860
ENV GRADIO_SERVER_NAME="0.0.0.0"
CMD ["python", "-m", "app"]

#CMD ["/bin/sh", "-c", "bash"]
