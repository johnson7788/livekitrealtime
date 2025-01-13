export type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
};

// 这些值应该从环境变量获取
const BASE_URL = process.env.REACT_APP_LIVEKIT_INTERVIEW_API;

type TokenResponse = {
  code: number;
  msg: string;
  data: {
    token: string;
    LIVEKIT_URL: string;
  };
};

export async function getConnectionDetails(): Promise<ConnectionDetails> {
  if (!BASE_URL) {
    throw new Error("Interview BASE_URL configuration is missing");
  }

  const participantIdentity = `voice_assistant_user_${Math.floor(Math.random() * 10_000)}`;
  const roomName = `voice_assistant_room_${Math.floor(Math.random() * 10_000)}`;
  
  // 从API获取token和LIVEKIT_URL
  const response = await fetch(
    `${BASE_URL}/api/getToken?user_name=${participantIdentity}&room_name=${roomName}`
  );
  const tokenData: TokenResponse = await response.json();
  
  if (tokenData.code !== 0) {
    throw new Error(`Failed to get token: ${tokenData.msg}`);
  }

  return {
    serverUrl: tokenData.data.LIVEKIT_URL,
    roomName,
    participantToken: tokenData.data.token,
    participantName: participantIdentity,
  };
}