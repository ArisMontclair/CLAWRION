"""
Fish S2 Pro Voice Agent — Pipecat Pipeline
Real-time conversational voice AI with Smart Turn detection.

Pipeline: Mic → Whisper STT → Smart Turn v3 → OpenRouter LLM → Fish S2 TTS → Speakers
"""

import os
from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.whisper.stt import WhisperSTTService, Model
from pipecat.services.openrouter.llm import OpenRouterLLMService
from pipecat.services.fish.audio.tts import FishAudioTTSService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.turns.user_stop import TurnAnalyzerUserTurnStopStrategy
from pipecat.turns.user_turn_strategies import UserTurnStrategies

load_dotenv(override=True)

# ─── System Prompt ──────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are a helpful, friendly voice assistant. Keep responses concise and conversational — \
this is a voice conversation, not a written essay. Use natural speech patterns.

You can use emotion tags to make your speech more expressive. Available tags: \
[whisper] [excited] [angry] [laughing] [sad] [shocked] [pause] [emphasis] [sigh] \
[shouting] [low voice] [singing].

For example: "That's [excited] amazing news!" or "[whisper] I have a secret to tell you."

Respond in the same language the user speaks to you. \
If they speak Dutch, respond in Dutch. If English, respond in English.\
"""

# ─── Transport Config ──────────────────────────────────────────
# Daily for production, SmallWebRTC for local dev (no API keys)
transport_params = {
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        audio_in_sample_rate=16000,
        audio_out_sample_rate=24000,
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        audio_in_sample_rate=16000,
        audio_out_sample_rate=24000,
    ),
}


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    """Main Pipecat pipeline."""

    # ─── STT: Faster-Whisper (local GPU) ────────────────────────
    whisper_model = os.getenv("WHISPER_MODEL", "large-v3")

    stt = WhisperSTTService(
        device="cuda",
        compute_type="float16",
        settings=WhisperSTTService.Settings(
            model=Model.LARGE if whisper_model == "large-v3" else Model.MEDIUM,
            language="",  # auto-detect
        ),
    )

    # ─── LLM: OpenRouter ───────────────────────────────────────
    llm_model = os.getenv("LLM_MODEL", "xiaomi/mimo-v2-pro")

    llm = OpenRouterLLMService(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model=llm_model,
        system_instruction=SYSTEM_PROMPT,
    )

    # ─── TTS: Fish Audio S2 Pro ────────────────────────────────
    tts = FishAudioTTSService(
        api_key=os.getenv("FISH_API_KEY"),
        voice_id=os.getenv("FISH_VOICE_ID", ""),
        model="s2-pro",
        params=FishAudioTTSService.InputParams(
            sample_rate=24000,
        ),
    )

    # ─── Context + Smart Turn v3 ───────────────────────────────
    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            user_turn_strategies=UserTurnStrategies(
                stop=[
                    TurnAnalyzerUserTurnStopStrategy(
                        turn_analyzer=LocalSmartTurnAnalyzerV3()
                    )
                ]
            ),
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )

    # ─── Pipeline ──────────────────────────────────────────────
    # Order matters: input → STT → aggregate → LLM → TTS → output
    pipeline = Pipeline([
        transport.input(),
        stt,
        user_aggregator,
        llm,
        tts,
        transport.output(),
        assistant_aggregator,
    ])

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
    )

    # ─── Event Handlers ────────────────────────────────────────
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected — starting conversation")
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    # ─── Run ───────────────────────────────────────────────────
    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Entry point for Pipecat runner."""
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main
    main()
