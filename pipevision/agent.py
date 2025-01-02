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
from livekit.plugins import openai, deepgram, silero
from livekit.plugins import cartesia, deepgram, openai, silero
from openai import AsyncClient
from livekit import rtc  #访问 LiveKit 的视频功能
from livekit.agents.llm import ChatMessage, ChatImage


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

async def get_video_track(room: rtc.Room):
    """搜索所有参与者以查找可用的视频轨道, Find and return the first available remote video track in the room."""
    for participant_id, participant in room.remote_participants.items():
        for track_id, track_publication in participant.track_publications.items():
            if track_publication.track and isinstance(
                track_publication.track, rtc.RemoteVideoTrack
            ):
                logger.info(
                    f"Found video track {track_publication.track.sid} "
                    f"from participant {participant_id}"
                )
                return track_publication.track
    raise ValueError("No remote video track found in the room")

async def get_latest_image(room: rtc.Room):
    """添加帧捕获功能, Capture and return a single frame from the video track."""
    video_stream = None
    try:
        video_track = await get_video_track(room)
        video_stream = rtc.VideoStream(video_track)
        async for event in video_stream:
            logger.debug("Captured latest video frame")
            return event.frame
    except Exception as e:
        logger.error(f"Failed to get latest image: {e}")
        return None
    finally:
        if video_stream:
            await video_stream.aclose()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit that can both see and hear. "
            "You should use short and concise responses, avoiding unpronounceable punctuation. "
            "When you see an image in our conversation, naturally incorporate what you see "
            "into your response. Keep visual descriptions brief but informative."
        ),
    )

    async def before_llm_cb(assistant: VoicePipelineAgent, chat_ctx: llm.ChatContext):
        """
        此回调是高效上下文管理的关键 - 它仅在助手即将响应时添加视觉信息。如果将视觉信息添加到每条消息中，它将很快填满LLMs上下文窗口。
        Callback that runs right before the LLM generates a response.
        Captures the current video frame and adds it to the conversation context.
        """
        latest_image = await get_latest_image(assistant.room)
        if latest_image:
            image_content = [ChatImage(image=latest_image)]
            chat_ctx.messages.append(ChatMessage(role="user", content=image_content))
            logger.debug("Added latest frame to conversation context")

    logger.info(f"connecting to room {ctx.room.name}")
    # await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL) #  不仅仅音频，还包括视频

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
        stt=deepgram.STT(http_session=http_session),
        llm=openai.LLM(model=os.environ["OPENAI_API_MODEL"],base_url=os.environ["OPENAI_API_BASE_URL"],api_key=os.environ["OPENAI_API_KEY"], client=openai_async_client),
        tts=cartesia.TTS(http_session=http_session),
        chat_ctx=initial_ctx,
        before_llm_cb=before_llm_cb
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
