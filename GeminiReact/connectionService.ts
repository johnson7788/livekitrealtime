import {
    AccessToken,
    AccessTokenOptions,
    VideoGrant,
  } from "livekit-server-sdk";
  //livekit-server-sdk是server端的，如果变成浏览器端?
  
  export type ConnectionDetails = {
    serverUrl: string;
    roomName: string;
    participantName: string;
    participantToken: string;
  };
  
  // 这些值应该从环境变量获取
  const API_KEY = process.env.REACT_APP_LIVEKIT_API_KEY;
  const API_SECRET = process.env.REACT_APP_LIVEKIT_API_SECRET;
  const LIVEKIT_URL = process.env.REACT_APP_LIVEKIT_URL;
  
  export async function getConnectionDetails(): Promise<ConnectionDetails> {
    if (!LIVEKIT_URL || !API_KEY || !API_SECRET) {
      throw new Error("LiveKit configuration is missing");
    }
  
    const participantIdentity = `voice_assistant_user_${Math.floor(Math.random() * 10_000)}`;
    const roomName = `voice_assistant_room_${Math.floor(Math.random() * 10_000)}`;
    
    const participantToken = await createParticipantToken(
      { identity: participantIdentity },
      roomName
    );
  
    return {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken,
      participantName: participantIdentity,
    };
  }
  
  function createParticipantToken(
    userInfo: AccessTokenOptions,
    roomName: string
  ) {
    if (!API_KEY || !API_SECRET) {
      throw new Error("LiveKit configuration is missing");
    }
  
    const at = new AccessToken(API_KEY, API_SECRET, {
      ...userInfo,
      ttl: "15m",
    });
    
    const grant: VideoGrant = {
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canPublishData: true,
      canSubscribe: true,
    };
    
    at.addGrant(grant);
    return at.toJwt();
  }