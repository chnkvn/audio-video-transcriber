import time
from pathlib import Path
from typing import Union
import gradio as gr
import torch
import yt_dlp as youtube_dl
from attrs import define
from faster_whisper import WhisperModel
from icecream import ic

# Variables
FILE_LIMIT_MB = 1000
YT_LENGTH_LIMIT_S = 3600


# Model
@define
class Model:
    language: str = "en"
    _model: Union[WhisperModel, None] = None

    @property
    def model(self):
        """Initialize a model depending on the language.
        - en : Initialize faster-distil-whisper-large-v2
        - fr : Initialize whisper-large-v3-french-distil-dec16
        NB : faster-distil-whisper-large-v3 is prone to hallucinate more often
        than faster-distil-whisper-large-v2.
        """

        if not self._model:
            if self.language == "fr":
                model_path = "./models/whisper-large-v3-french-distil-dec16/ctranslate2"
            else:  # english
                model_path = "./models/faster-distil-whisper-large-v2"
            # Initialize model
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type_dict = {"cuda": "float16", "cpu": "int8"}
            self._model = WhisperModel(
                model_path,
                device=device,
                compute_type=compute_type_dict[device],
            )
        return self._model

    def transcribe_media(
        self,
        mediapath: Union[str, Path] = "../tests/test_en.mp3",
        timestamp=True,
        save=True,
    ):
        """Transcribe a media using model"""
        if mediapath.startswith("https://"):
            mediapath = download_yt_audio(mediapath)
        segments, info = self.model.transcribe(
            mediapath,
            beam_size=5,
            language=self.language,
            condition_on_previous_text=False,
        )
        transcript = ""
        if timestamp:
            for segment in segments:
                formatted_segment = "[%.2fs -> %.2fs] %s" % (
                    segment.start,
                    segment.end,
                    segment.text,
                )
                transcript += formatted_segment + "\n"
        else:
            for segment in segments:
                transcript += segment.text.strip() + "\n"
        if save:
            output_file_name = f'{mediapath.split("/").pop()}.txt'.replace(" ", "_")
            self.save_transcript(transcript, output_file_name)
        return transcript

    def save_transcript(self, transcript, output_file_name):
        """Save transcript in the output folder"""
        # Create outputs folder if it does not exist
        Path("outputs").mkdir(parents=True, exist_ok=True)
        with open(Path("outputs", output_file_name), "w") as f:
            print(transcript, file=f)
        return


# Download a youtube video
def download_yt_audio(yt_url):
    info_loader = youtube_dl.YoutubeDL()
    Path("dl").mkdir(parents=True, exist_ok=True)
    try:
        info = info_loader.extract_info(yt_url, download=False)
        filename = str(Path("dl", f"{info['title']}.mp4"))
    except youtube_dl.utils.DownloadError as err:
        raise gr.Error(str(err))

    file_length = info["duration_string"]
    file_h_m_s = file_length.split(":")
    file_h_m_s = [int(sub_length) for sub_length in file_h_m_s]

    if len(file_h_m_s) == 1:
        file_h_m_s.insert(0, 0)
    if len(file_h_m_s) == 2:
        file_h_m_s.insert(0, 0)
    file_length_s = file_h_m_s[0] * 3600 + file_h_m_s[1] * 60 + file_h_m_s[2]

    if file_length_s > YT_LENGTH_LIMIT_S:
        yt_length_limit_hms = time.strftime(
            "%HH:%MM:%SS", time.gmtime(YT_LENGTH_LIMIT_S)
        )
        file_length_hms = time.strftime("%HH:%MM:%SS", time.gmtime(file_length_s))
        raise gr.Error(
            f"Maximum YouTube length is {yt_length_limit_hms},"
            f" got {file_length_hms} YouTube video."
        )
    ydl_opts = {
        "outtmpl": filename,
        "format": "worstvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([yt_url])
            return filename
        except youtube_dl.utils.ExtractorError as err:
            raise gr.Error(err(str))

    
if __name__ == "__main__":
    yt_url = "https://youtu.be/iA8XwKOD8qg"
    model = Model()
    print(model.transcribe_media(timestamp=False))