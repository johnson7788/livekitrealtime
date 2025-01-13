import {
  LiveKitRoom,
  useVoiceAssistant,
  BarVisualizer,
  RoomAudioRenderer,
  VoiceAssistantControlBar,
  AgentState,
  DisconnectButton,
} from "@livekit/components-react";
import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { NoAgentNotification } from "./NoAgentNotification";
import { CloseIcon } from "./CloseIcon";
// import { useKrispNoiseFilter } from "@livekit/components-react/dist/krisp";
import { ConnectionDetails, getConnectionDetails } from "./connectionService";

function GeminiReact() {
  const [connectionDetails, updateConnectionDetails] = useState(undefined);
  const [agentState, setAgentState] = useState("disconnected");

  const onConnectButtonClicked = useCallback(async () => {
    try {
      const details = await getConnectionDetails();
      updateConnectionDetails(details);
    } catch (error) {
      console.error("Failed to get connection details:", error);
    }
  }, []);

  return (
    <main
      data-lk-theme="default"
      className="h-full grid content-center bg-[var(--lk-bg)]"
    >
      <LiveKitRoom
        token={connectionDetails?.participantToken}
        serverUrl={connectionDetails?.serverUrl}
        connect={connectionDetails !== undefined}
        audio={true}
        video={false}
        onMediaDeviceFailure={onDeviceFailure}
        onDisconnected={() => {
          updateConnectionDetails(undefined);
        }}
        className="grid grid-rows-[2fr_1fr] items-center"
      >
        <SimpleVoiceAssistant onStateChange={setAgentState} />
        <ControlBar
          onConnectButtonClicked={onConnectButtonClicked}
          agentState={agentState}
        />
        <RoomAudioRenderer />
        <NoAgentNotification state={agentState} />
      </LiveKitRoom>
    </main>
  );
}


function SimpleVoiceAssistant({ onStateChange }) {
  const { state, audioTrack } = useVoiceAssistant();

  useEffect(() => {
    onStateChange(state);
  }, [onStateChange, state]);

  return (
    <div className="h-[300px] max-w-[90vw] mx-auto">
      <BarVisualizer
        state={state}
        barCount={5}
        trackRef={audioTrack}
        className="agent-visualizer"
        options={{ minHeight: 24 }}
      />
    </div>
  );
}

function ControlBar({ onConnectButtonClicked, agentState }) {
  // const krisp = useKrispNoiseFilter();

  // useEffect(() => {
  //   krisp.setNoiseFilterEnabled(true);
  // }, [krisp]);

  return (
    <div className="relative h-[100px]">
      <AnimatePresence>
        {agentState === "disconnected" && (
          <motion.button
            initial={{ opacity: 0, top: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, top: "-10px" }}
            transition={{ duration: 1, ease: [0.09, 1.04, 0.245, 1.055] }}
            className="uppercase absolute left-1/2 -translate-x-1/2 px-4 py-2 bg-white text-black rounded-md"
            onClick={onConnectButtonClicked}
          >
            Start a conversation
          </motion.button>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {agentState !== "disconnected" &&
          agentState !== "connecting" && (
            <motion.div
              initial={{ opacity: 0, top: "10px" }}
              animate={{ opacity: 1, top: 0 }}
              exit={{ opacity: 0, top: "-10px" }}
              transition={{ duration: 0.4, ease: [0.09, 1.04, 0.245, 1.055] }}
              className="flex h-8 absolute left-1/2 -translate-x-1/2 justify-center"
            >
              <VoiceAssistantControlBar controls={{ leave: false }} />
              <DisconnectButton>
                <CloseIcon />
              </DisconnectButton>
            </motion.div>
          )}
      </AnimatePresence>
    </div>
  );
}

function onDeviceFailure(error) {
  console.error(error);
  alert(
    "Error acquiring camera or microphone permissions. Please make sure you grant the necessary permissions in your browser and reload the tab"
  );
}

export default GeminiReact;
