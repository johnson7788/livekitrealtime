from __future__ import annotations

import logging
import os
import aiohttp

from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai


load_dotenv(dotenv_path=".env")
logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

class ProxySession(aiohttp.ClientSession):
    def __init__(self, proxy_url, *args, **kwargs):
        connector = aiohttp.TCPConnector(ssl=False)  # 设置基础连接器
        super().__init__(*args, connector=connector, **kwargs)
        self._default_proxy = proxy_url  # 设置默认代理

    async def _request(self, method, url, **kwargs):
        if "proxy" not in kwargs:
            kwargs["proxy"] = self._default_proxy  # 将默认代理注入到请求中
        return await super()._request(method, url, **kwargs)

async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    if os.environ.get("USE_PROXY") == "true":
        proxy_url = os.environ["PROXY_URL"]
        http_session = ProxySession(proxy_url)
    else:
        http_session = aiohttp.ClientSession()

    participant = await ctx.wait_for_participant()

    run_multimodal_agent(ctx, participant, http_session)

    logger.info("agent started")


def run_multimodal_agent(ctx: JobContext, participant: rtc.RemoteParticipant, http_session):
    logger.info("starting multimodal agent")

    model = openai.realtime.RealtimeModel(
        instructions=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation. "
            "You were created as a demo to showcase the capabilities of LiveKit's agents framework."
        ),
        modalities=["audio", "text"],
        http_session = http_session

    )
    agent = MultimodalAgent(model=model)
    agent.start(ctx.room, participant)

    session = model.sessions[0]
    session.conversation.item.create(
        llm.ChatMessage(
            role="assistant",
            content="Please begin the interaction with the user in a manner consistent with your instructions.",
        )
    )
    session.response.create()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
