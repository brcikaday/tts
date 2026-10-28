"""Opt-in live checks (uses configured Khaya/Groq credentials and API quota).

Run from repository root: python -m tests.live_provider_smoke
Audio is written only to a temporary directory. No database records are created.
"""
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import requests
from core.config import settings
from services import detection_service, tts_service, ai_service, podcast_service


def main():
    original_post = requests.post
    original_load_groq = ai_service.load_groq

    def bounded_post(*args, **kwargs):
        kwargs.setdefault("timeout", 30)
        return original_post(*args, **kwargs)

    def bounded_groq():
        return original_load_groq().with_options(timeout=30, max_retries=0)

    asyncio.run(detection_service.load_model())
    detected = detection_service.detect_risky_words("Photosynthesis converts sunlight into energy.")
    assert isinstance(detected, list)
    print("PASS: real BERT model loads and performs inference", flush=True)
    failures = 0
    with tempfile.TemporaryDirectory() as audio_dir, \
            patch.object(settings, "AUDIO_STORAGE_PATH", audio_dir), \
            patch("requests.post", side_effect=bounded_post), \
            patch("services.ai_service.load_groq", side_effect=bounded_groq), \
            patch("services.podcast_service.load_groq", side_effect=bounded_groq):
        checks = [
            ("Khaya pipeline and audio", lambda: tts_service.process_tts("Water is important for life.", "twi", "Kofi")),
            ("Groq summary with Khaya translation", lambda: ai_service.summarise_text("Water is important for life. Plants need water.", "twi")),
            ("Groq Q&A", lambda: ai_service.ask_question("Plants need water.", "What do plants need?")),
            ("Groq podcast with Khaya audio", lambda: podcast_service.process_podcast("Plants need water to grow.", "twi", "Kofi", "Akua")),
        ]
        for name, check in checks:
            try:
                result = check()
                if isinstance(result, tuple):
                    assert Path(audio_dir, result[0].split("/")[-1]).exists()
                    assert result[1] > 0
                else:
                    assert result
                print("PASS:", name, flush=True)
            except Exception as exc:
                failures += 1
                # Never print provider exception bodies, credentials, or headers.
                print("FAIL:", name, type(exc).__name__, "status=", getattr(exc, "status_code", None), flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
