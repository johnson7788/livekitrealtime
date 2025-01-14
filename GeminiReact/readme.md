不使用nextjs实现，直接获取客户端的token,后端如下

获取Token
@app.api_route('/api/getToken', methods=["GET", "POST"])
async def getToken(request: Request, user_name: str = Query(), room_name: str = Query()):
    """
    curl -X GET "http://127.0.0.1:5321/api/getToken?user_name=test_user&room_name=test_room"
    curl -X POST "http://127.0.0.1:5321/api/getToken" -H "Content-Type: application/json" -d '{"user_name": "test_user", "room_name": "test_room"}'
    获取token
    - 如果是 GET 请求：`user_name` 和 `room_name` 从查询参数获取
    - 如果是 POST 请求：`user_name` 和 `room_name` 从请求体中获取
    """
    metadata = {"instructions": "You are a helpful assistant, your name is Ava."}
    if request.method == "POST":
        body = await request.json()
        user_name = body.get("user_name", user_name)
        room_name = body.get("room_name", room_name)
        metadata = body.get("metadata", metadata)
    if not user_name or not room_name:
        logging.error("user_name or room_name is not set")
        return {"code": 4001, "msg": "user_name or room_name is not set", "data": ""}
    LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY')
    LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET')
    LIVEKIT_URL = os.getenv('LIVEKIT_URL')
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET or not LIVEKIT_URL:
        logging.error("LIVEKIT_API_KEY or LIVEKIT_API_SECRET or LIVEKIT_URL is not set")
        return {"code": 4002, "msg": "LIVEKIT_API_KEY or LIVEKIT_API_SECRET is not set", "data": ""}
    logging.info(f"user_name: {user_name}, room_name: {room_name}, API_KEY: {LIVEKIT_API_KEY}, API_SECRET: {LIVEKIT_API_SECRET}")
    token = api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET) \
        .with_identity(user_name) \
        .with_name(user_name) \
        .with_metadata(json.dumps(metadata, ensure_ascii=False)) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        ))
    token_jwt = token.to_jwt()
    data = {
        "token": token_jwt,
        "LIVEKIT_URL": LIVEKIT_URL,
    }
    return {"code": 0, "msg": "success", "data": data}



后端Agent
async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")
    metadata = json.loads(participant.metadata)
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=metadata.get("instructions", "You are a helpful assistant."),
    )
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
