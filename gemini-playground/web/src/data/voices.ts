export enum VoiceId {
  charon = "Charon",
  puck = "Puck",
  kore = "Kore",
  fenrir = "Fenrir",
  aoede = "Aoede"
}

export interface Voice {
  id: VoiceId;
  name: string;
}

export const voices: Voice[] = [
  {
    id: VoiceId.charon,
    name: "Charon",
  },
  {
    id: VoiceId.puck,
    name: "Puck",
  },
  {
    id: VoiceId.kore,
    name: "Kore",
  },
  {
    id: VoiceId.fenrir,
    name: "Fenrir",
  },
  {
    id: VoiceId.aoede,
    name: "Aoede",
  },
];
