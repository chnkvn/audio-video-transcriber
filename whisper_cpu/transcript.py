from faster_whisper import WhisperModel
import torch
from icecream import ic
from attrs import define
from typing import Union
from pathlib import Path, PurePath
from glob import glob


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

    def transcribe_media(self, mediapath: Union[str, Path] = "tests/test_en.mp3"):
        """Transcribe a media using model"""

        # Create outputs folder if it does not exist
        Path("outputs").mkdir(parents=True, exist_ok=True)
        output_file_name = f'{mediapath.split("/").pop()}.txt'
        segments, info = self.model.transcribe(
            mediapath,
            beam_size=5,
            language=self.language,
            condition_on_previous_text=False,
        )
        transcript = ""
        for segment in segments:
            formatted_segment = "[%.2fs -> %.2fs] %s" % (
                segment.start,
                segment.end,
                segment.text,
            )
            transcript += formatted_segment
            #ic(formatted_segment)
        """
        with open(Path("outputs", output_file_name), 'w') as f:
            for segment in segments:
                print(
                    "[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text),
                    sep='\n',
                    file=f
                )"""
        return transcript


if __name__ == "__main__":
    model = Model()
    print(model.transcribe_media())
