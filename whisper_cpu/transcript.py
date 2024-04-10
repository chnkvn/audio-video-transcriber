import time
from pathlib import Path
from typing import Union
import gradio as gr
import torch
import yt_dlp as youtube_dl
from attrs import define
from faster_whisper import WhisperModel
from icecream import ic
import tempfile

# Variables
FILE_LIMIT_MB = 1000
YT_LENGTH_LIMIT_S = 3600
AVAILABLE_LANGUAGES = ["English", "French"]


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
        - multi : Initialize whisper-large-v2. Slower results.
        NB : whisper-large-v3 is prone to hallucinate more often
        than whisper-large-v2.
        """

        if not self._model:
            if self.language == "fr":
                model_path = "models/whisper-large-v3-french-distil-dec16/ctranslate2"
            elif self.language == "multi":
                model_path = "models/faster-whisper-large-v2"
            else:  # english
                model_path = "models/faster-distil-whisper-large-v2"
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
        mediapath: Union[str, Path],
    ):
        """Transcribe a media using model"""
        if mediapath.startswith("https://"):
            mediapath = download_yt_audio(mediapath)
        segments, info = self.model.transcribe(
            mediapath,
            beam_size=5,
            # language=self.language
            condition_on_previous_text=False,
        )
        transcript = ""
        no_ts_transcript = ""
        for segment in segments:
            formatted_segment = "[%.2fs -> %.2fs] %s" % (
                segment.start,
                segment.end,
                segment.text,
            )
            transcript += formatted_segment + "\n"
            no_ts_transcript += segment.text.strip() + "\n"
            ic(formatted_segment)
        return transcript, no_ts_transcript


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


# Process
def main(language: str, media: Union[str, Path] = "../tests/test_en.mp3"):
    """Choose a language to load a model
    eventually download the media and transcribe it."""
    models_dict = {
        "French": Model(language="fr"),
        "English": Model(),
        "Multilingual": Model(language="multi"),
    }
    model = models_dict.get(language, "English")
    transcript, no_ts_transcript = model.transcribe_media(media)
    return transcript, no_ts_transcript


# Define function to save output to a file
def save_output_to_file(output_text):
    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", suffix=".txt"
    ) as temp_file:
        temp_file.write(output_text)
        return temp_file.name


# Function to handle download
def download_output(output_text):
    file_path = save_output_to_file(output_text)
    return file_path


# Interface
def run_app():
    gr.close_all()
    demo = gr.Blocks(title="Media transcriber")
    yt = gr.Interface(
        fn=main,
        inputs=[
            gr.Radio(
                ["English", "French", "Multilingual"],
                label="language",
                value="English",
                info="If possible, opt for the Engligh or the French model. "
                "The multilingual model is a slower model "
                "that works more slowly than others.",
            ),
            gr.Textbox(
                label="media",
                value="https://youtu.be/XrZPLF0ezw8",
            ),
        ],
        outputs=[
            gr.Textbox(label="transcript without timestamps"),
            gr.Textbox(label="transcript with timestamps"),
        ],
        title="Transcribe YouTube videos using Distill-whisper",
        description=(
            "Transcribe long-form YouTube videos with the click of a button! "
            "The model may have a hard time with background sounds/voices "
            "and proper nouns, so check the results!"
        ),
    )
    local_file = gr.Interface(
        fn=main,
        inputs=[
            gr.Radio(
                ["English", "French", "Multilingual"],
                label="language",
                value="English",
                info="If possible, opt for the Engligh or the French model. "
                "The multilingual model is a slower model "
                "that works more slowly than others.",
            ),
            gr.File(label="media", file_types=["audio", "video"]),
        ],
        outputs=[
            gr.Textbox(label="transcript without timestamps"),
            gr.Textbox(label="transcript with timestamps"),
        ],
        title="Transcribe a local audio file using Distill-whisper",
        description=(
            "Transcribe a local audio file with the click of a button! "
            "The model may have a hard time with background sounds/voices "
            "and proper nouns, so check the results!"
        ),
    )
    with demo:
        gr.TabbedInterface(
            [yt, local_file], ["Youtube transcriber", "Local file transcriber"]
        )
    demo.launch()


if __name__ == "__main__":
    run_app()
