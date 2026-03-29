"""
Orpheus TTS Service for Pipecat
Connects to the CLAWRION server's Orpheus TTS HTTP endpoint (POST /v1/tts).
"""

from dataclasses import dataclass
from typing import AsyncGenerator, Optional

import aiohttp
from loguru import logger

from pipecat.frames.frames import (
    ErrorFrame,
    Frame,
    TTSStoppedFrame,
)
from pipecat.services.settings import TTSSettings
from pipecat.services.tts_service import TTSService
from pipecat.utils.tracing.service_decorators import traced_tts


@dataclass
class OrpheusTTSSettings(TTSSettings):
    voice: str = "tara"


class OrpheusTTS(TTSService):
    """Pipecat TTS service for Orpheus TTS via CLAWRION server."""

    Settings = OrpheusTTSSettings
    _settings: Settings

    def __init__(
        self,
        *,
        base_url: str,
        aiohttp_session: aiohttp.ClientSession,
        voice: str = "tara",
        settings: Optional[Settings] = None,
        **kwargs,
    ):
        default_settings = self.Settings(model=None, voice=voice, language=None)
        if settings is not None:
            default_settings.apply_update(settings)

        super().__init__(
            push_start_frame=True,
            push_stop_frames=True,
            settings=default_settings,
            **kwargs,
        )

        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self._base_url = base_url
        self._session = aiohttp_session
        logger.info(f"OrpheusTTS initialized: {self._base_url}/v1/tts (voice={voice})")

    def can_generate_metrics(self) -> bool:
        return True

    @traced_tts
    async def run_tts(
        self, text: str, context_id: str
    ) -> AsyncGenerator[Frame, None]:
        logger.debug(f"{self}: Generating TTS [{text}]")

        url = f"{self._base_url}/v1/tts"
        payload = {
            "text": text,
            "voice": self._settings.voice,
        }

        try:
            async with self._session.post(
                url, json=payload, headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    logger.error(f"Orpheus TTS error ({response.status}): {error}")
                    yield ErrorFrame(error=f"TTS error: {response.status} {error}")
                    yield TTSStoppedFrame(context_id=context_id)
                    return

                await self.start_tts_usage_metrics(text)

                async for frame in self._stream_audio_frames_from_iterator(
                    response.content.iter_chunked(self.chunk_size),
                    strip_wav_header=True,
                    context_id=context_id,
                ):
                    await self.stop_ttfb_metrics()
                    yield frame

        except Exception as e:
            logger.error(f"{self} exception: {e}")
            yield ErrorFrame(error=f"TTS error: {e}")
        finally:
            await self.stop_ttfb_metrics()
