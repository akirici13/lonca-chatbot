import whisper

def transcribe_audio(audio_path: str) -> str:
    model = whisper.load_model("small")
    result = model.transcribe(audio_path)
    return result['text'] 