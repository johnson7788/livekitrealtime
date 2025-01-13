import logging
import os
import aiohttp
import httpx

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import cartesia, deepgram, openai, silero,azure
from openai import AsyncClient


load_dotenv(dotenv_path=".env")
logger = logging.getLogger("voice-agent")


class ProxySession(aiohttp.ClientSession):
    def __init__(self, proxy_url, *args, **kwargs):
        connector = aiohttp.TCPConnector(ssl=False)  # 设置基础连接器
        super().__init__(*args, connector=connector, **kwargs)
        self._default_proxy = proxy_url  # 设置默认代理

    async def _request(self, method, url, **kwargs):
        if "proxy" not in kwargs:
            kwargs["proxy"] = self._default_proxy  # 将默认代理注入到请求中
        return await super()._request(method, url, **kwargs)


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation. "
            "You were created as a demo to showcase the capabilities of LiveKit's agents framework."
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    if os.environ.get("USE_PROXY") == "true":
        proxy_url = os.environ["PROXY_URL"]
        http_session = ProxySession(proxy_url)
        http_client = httpx.AsyncClient(proxy=proxy_url)
        openai_async_client = AsyncClient(http_client=http_client)
    else:
        http_session = aiohttp.ClientSession()
        http_client = httpx.AsyncClient()
        openai_async_client = AsyncClient(http_client=http_client)
    # This project is configured to use Deepgram STT, OpenAI LLM and TTS plugins
    # Other great providers exist like Cartesia and ElevenLabs
    # Learn more and pick the best one for your app:
    # https://docs.livekit.io/agents/plugins
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=azure.STT(),
        llm=openai.LLM.with_azure(model="gpt-4o-mini"),
        tts=azure.TTS(),
        chat_ctx=initial_ctx,
    )

    agent.start(ctx.room, participant)

    # The agent should be polite and greet the user when it joins :)
    await agent.say("Hey, how can I help you today?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
