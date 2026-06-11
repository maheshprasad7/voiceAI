const stateIndicator = document.getElementById('stateIndicator');
const transcriptText = document.getElementById('transcriptText');
const responseText = document.getElementById('responseText');
const sttLatency = document.getElementById('sttLatency');
const totalLatency = document.getElementById('totalLatency');
const logContainer = document.getElementById('logContainer');
const siriOrb = document.getElementById('siriOrb');

function addLog(message) {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    const logEl = document.createElement('div');
    logEl.innerText = `[${time}] ${message}`;
    logContainer.prepend(logEl);
}

function updateOrbState(state) {
    // Remove all state classes
    siriOrb.className = 'orb';
    
    // Add specific state class
    if (state === 'IDLE') siriOrb.classList.add('idle');
    else if (state === 'LISTENING') siriOrb.classList.add('listening');
    else if (state === 'TRANSCRIBING') siriOrb.classList.add('transcribing');
    else if (state === 'THINKING') siriOrb.classList.add('thinking');
    else if (state === 'SPEAKING') siriOrb.classList.add('speaking');
    else siriOrb.classList.add('offline');
}

function connect() {
    const ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onopen = () => {
        addLog("WebSocket connected to AVAHAAN Voice Core.");
    };

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        
        if (msg.type === 'state') {
            stateIndicator.innerText = msg.data;
            updateOrbState(msg.data);
            
            // Clear texts on new turn
            if (msg.data === 'LISTENING') {
                transcriptText.innerText = "Listening...";
                responseText.innerText = "";
            }
        } 
        else if (msg.type === 'transcript') {
            transcriptText.innerText = `"${msg.data}"`;
        }
        else if (msg.type === 'latency_stt') {
            sttLatency.innerText = `${msg.data.toFixed(2)}s`;
        }
        else if (msg.type === 'latency_total') {
            totalLatency.innerText = `${msg.data.toFixed(2)}s`;
        }
    };

    ws.onclose = () => {
        addLog("WebSocket disconnected. Retrying in 3s...");
        stateIndicator.innerText = "OFFLINE";
        updateOrbState("OFFLINE");
        setTimeout(connect, 3000);
    };
    
    ws.onerror = () => {
        ws.close();
    };
}

// Start connection
connect();
