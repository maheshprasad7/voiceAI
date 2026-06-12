const statusLabel = document.getElementById('statusLabel');
const transcriptList = document.getElementById('transcriptList');
const transcriptSection = document.getElementById('transcriptSection');
const logContainer = document.getElementById('logContainer');
const siriOrb = document.getElementById('siriOrb');

// Track current partial transcripts by participant
const activeTranscripts = {};
let currentRoom = null;

function addLog(message) {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    const logEl = document.createElement('div');
    logEl.innerText = `[${time}] ${message}`;
    logContainer.prepend(logEl);
}

function updateState(state) {
    statusLabel.innerText = state;
    siriOrb.className = 'orb';

    if (state === 'Connecting...') siriOrb.classList.add('connecting');
    else if (state === 'Listening') siriOrb.classList.add('listening');
    else if (state === 'Thinking') siriOrb.classList.add('thinking');
    else if (state === 'Speaking') siriOrb.classList.add('speaking');
    else siriOrb.classList.add('offline');
}

function addTranscriptEntry(speaker, text, isAgent, isPartial) {
    const key = isAgent ? 'agent' : 'user';

    if (activeTranscripts[key]) {
        const existing = activeTranscripts[key];
        existing.textEl.innerText = text;
        if (isPartial) {
            existing.textEl.classList.add('partial');
        } else {
            existing.textEl.classList.remove('partial');
            delete activeTranscripts[key];
        }
        scrollToBottom();
        return;
    }

    const entry = document.createElement('div');
    entry.className = `transcript-entry ${isAgent ? 'agent' : 'user'}`;

    const speakerEl = document.createElement('div');
    speakerEl.className = 'speaker';
    speakerEl.innerText = speaker;

    const textEl = document.createElement('div');
    textEl.className = 'text';
    textEl.innerText = text;

    if (isPartial) {
        textEl.classList.add('partial');
        activeTranscripts[key] = { entry, textEl };
    }

    entry.appendChild(speakerEl);
    entry.appendChild(textEl);
    transcriptList.appendChild(entry);
    scrollToBottom();
}

function scrollToBottom() {
    transcriptSection.scrollTop = transcriptSection.scrollHeight;
}

// ── LiveKit Room Connection ──
async function connectToLiveKit() {
    // Clean up previous room
    if (currentRoom) {
        try { currentRoom.disconnect(); } catch(e) {}
        currentRoom = null;
    }

    try {
        updateState('Connecting...');
        addLog("Requesting LiveKit token...");

        const res = await fetch('/token?t=' + Date.now());
        const data = await res.json();

        if (data.error) {
            addLog("Token error: " + data.error);
            updateState('Offline');
            setTimeout(connectToLiveKit, 5000);
            return;
        }

        addLog("Joining room: " + data.room);

        const room = new LivekitClient.Room({
            audioCaptureDefaults: { autoGainControl: true, noiseSuppression: true, echoCancellation: true },
            adaptiveStream: true,
            dynacast: true,
        });
        currentRoom = room;

        // ── Audio playback ──
        room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            if (track.kind === 'audio') {
                const audioEl = track.attach();
                audioEl.style.display = 'none';
                document.body.appendChild(audioEl);
                addLog("Agent audio connected.");
            }
        });

        // ── Active speakers → orb state ──
        room.on(LivekitClient.RoomEvent.ActiveSpeakersChanged, (speakers) => {
            const localParticipant = room.localParticipant;
            const agentSpeaking = speakers.some(s => s !== localParticipant);

            if (agentSpeaking) {
                updateState('Speaking');
            } else {
                updateState('Listening');
            }
        });

        // ── Live Transcription ──
        room.on(LivekitClient.RoomEvent.TranscriptionReceived, (segments, participant) => {
            if (!segments || segments.length === 0) return;

            const localParticipant = room.localParticipant;
            const isAgent = participant && participant !== localParticipant;
            const speaker = isAgent ? 'Friday' : 'You';

            for (const segment of segments) {
                const text = segment.text || '';
                if (!text.trim()) continue;
                const isPartial = segment.final === false;
                addTranscriptEntry(speaker, text, isAgent, isPartial);
            }
        });

        // ── Participant events ──
        room.on(LivekitClient.RoomEvent.ParticipantConnected, (participant) => {
            addLog("Agent joined: " + participant.identity);
            updateState('Listening');
        });

        room.on(LivekitClient.RoomEvent.ParticipantDisconnected, (participant) => {
            addLog("Agent left: " + participant.identity);
        });

        room.on(LivekitClient.RoomEvent.Disconnected, () => {
            addLog("Disconnected. Reconnecting in 2s...");
            updateState('Connecting...');
            currentRoom = null;
            setTimeout(connectToLiveKit, 2000);
        });

        // ── Connect and enable mic ──
        await room.connect(data.url, data.token);
        addLog("Connected to room: " + room.name);

        await room.localParticipant.setMicrophoneEnabled(true);
        addLog("Microphone enabled. Always listening.");

        updateState('Listening');

    } catch (err) {
        addLog("Error: " + err.message);
        console.error("LiveKit error:", err);
        updateState('Connecting...');
        setTimeout(connectToLiveKit, 3000);
    }
}

// Start on page load
connectToLiveKit();
