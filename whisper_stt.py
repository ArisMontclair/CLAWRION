"""
Whisper Remote STT Service for Pipecat
Calls a self-hosted Whisper server on Modal via HTTP.
No GPU needed on the bot machine.
"""

import io
import wave
from typing import AsyncGenerator

import aiohttp
from loguru import logger

from pipecat.frames.frames import (
    ErrorFrame,
    Frame,
    TranscriptionFrame,
)
from pipecat.services.stt_service import STTService
from pipecat.utils.tracing.service_decorators import traced_stt


class WhisperRemoteSTT(STTService):
    """Pipecat STT service for remote Whisper server (HTTP).

    Buffers audio and sends to Whisper when buffer is full or on flush.
    """

    def __init__(
        self,
        *,
        base_url: str,
        aiohttp_session: aiohttp.ClientSession,
        language: str = "",
        sample_rate: int = 16000,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self._base_url = base_url
        self._session = aiohttp_session
        self._language = language
        self._sample_rate = sample_rate
        self._audio_buffer = bytearray()
        self._buffer_duration_sec = 2.0
        self._buffer_max_bytes = int(sample_rate * 2 * self._buffer_duration_sec)

        logger.info(f"WhisperRemoteSTT initialized: {self._base_url}/v1/transcribe")

    def can_generate_metrics(self) -> bool:
        return True

    async def _transcribe_buffer(self) -> str | None:
        """Send buffered audio to Whisper and return transcribed text."""
        if not self._audio_buffer:
            return None

        buf = bytes(self._audio_buffer)
        self._audio_buffer.clear()

        # Convert PCM to WAV
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self._sample_rate)
            wf.writeframes(buf)
        wav_buffer.seek(0)

        # POST to Whisper
        data = aiohttp.FormData()
        data.add_field(
            "audio", wav_buffer,
            filename="audio.wav",
            content_type="audio/wav",
        )
        if self._language:
            data.add_field("language", self._language)

        url = f"{self._base_url}/v1/transcribe"
        async with self._session.post(url, data=data) as response:
            if response.status != 200:
                error = await response.text()
                logger.error(f"Whisper STT error ({response.status}): {error}")
                return None

            result = await response.json()
            return result.get("text", "").strip()

    @traced_stt
    async def run_stt(self, audio: bytes) -> AsyncGenerator[Frame, None]:
        """Buffer audio and transcribe when buffer is full.

        Args:
            audio: Raw PCM audio bytes (16-bit, mono).
        """
        self._audio_buffer.extend(audio)

        if len(self._audio_buffer) < self._buffer_max_bytes:
            return

        await self.start_processing_metrics()

        try:
            text = await self._transcribe_buffer()

            if text:
                logger.debug(f"Whisper STT: [{text}]")
                yield TranscriptionFrame(
                    text=text,
                    user_id="",
                    timestamp="",
                )
        except Exception as e:
            logger.error(f"WhisperRemoteSTT error: {e}")
            yield ErrorFrame(error=str(e))
        finally:
            await self.stop_processing_metrics()

    async def flush_audio(self):
        """Flush remaining audio in buffer.

        Called when the pipeline detects end of speech.
        Prevents losing the tail of an utterance.
        """
        if not self._audio_buffer:
            return

        # Need at least 0.5 sec of audio to bother transcribing
        min_bytes = int(self._sample_rate * 2 * 0.5)
        if len(self._audio_buffer) < min_bytes:
            self._audio_buffer.clear()
            return

        await self.start_processing_metrics()

        try:
            text = await self._transcribe_buffer()
            if text:
                logger.debug(f"Whisper STT (flush): [{text}]")
                yield TranscriptionFrame(
                    text=text,
                    user_id="",
                    timestamp="",
                )
        except Exception as e:
            logger.error(f"WhisperRemoteSTT flush error: {e}")
            yield ErrorFrame(error=str(e))
        finally:
            await self.stop_processing_metrics()
