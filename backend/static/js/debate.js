// Debate Roundtable Engine

let debateScript = [];
let currentLineIndex = 0;
let isDebateActive = false;
let audioQueue = [];
let isPlaying = false;
let recognitionDebate;

const debateOverlay = document.getElementById('debate-overlay');
const statusText = document.getElementById('debate-status');
const micButton = document.getElementById('debate-mic-btn');

// Initialize Speech Recognition
if ('webkitSpeechRecognition' in window) {
    recognitionDebate = new webkitSpeechRecognition();
    recognitionDebate.continuous = false;
    recognitionDebate.interimResults = false;

    recognitionDebate.onstart = () => {
        statusText.innerText = "Listening to you...";
        micButton.classList.add('recording');
    };

    recognitionDebate.onend = () => {
        micButton.classList.remove('recording');
    };

    recognitionDebate.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        statusText.innerText = `You said: "${transcript}"`;
        handleUserReply(transcript);
    };
} else {
    console.error("Speech Recognition Not Supported");
}

async function startDebate() {
    const articleText = document.getElementById('article-text-content').innerText;
    const articleUrl = new URLSearchParams(window.location.search).get('url');
    
    // Show Overlay
    document.getElementById('debate-overlay').classList.add('active');
    statusText.innerText = "Generating Script (Alex & Maya are prepping)...";
    
    try {
        const response = await fetch('/debate/init', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                text: articleText,
                url: articleUrl 
            })
        });
        
        const data = await response.json();
        
        if (data.script) {
            debateScript = data.script;
            currentLineIndex = 0;
            statusText.innerText = "Starting Debate...";
            playNextLine();
        } else {
            statusText.innerText = "Error: Could not generate debate.";
        }
        
    } catch (err) {
        console.error(err);
        statusText.innerText = "Connection Error.";
    }
}

async function playNextLine() {
    if (currentLineIndex >= debateScript.length) {
        finishDebate();
        return;
    }

    const line = debateScript[currentLineIndex];
    updateVisuals(line.speaker, true);
    statusText.innerText = `${line.speaker} is speaking...`;

    try {
        // Fetch Audio
        const audioResponse = await fetch('/debate/audio', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ text: line.text, speaker: line.speaker })
        });

        if (!audioResponse.ok) throw new Error("Audio Failed");

        const blob = await audioResponse.blob();
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);

        audio.onended = () => {
            updateVisuals(line.speaker, false);
            currentLineIndex++;
            // Add a natural 1.2 second pause before the next person speaks
            statusText.innerText = "Brief pause...";
            setTimeout(() => {
                playNextLine(); 
            }, 1200);
        };

        audio.play();

    } catch (err) {
        console.error(err);
        statusText.innerText = "Audio Error. Skipping line.";
        currentLineIndex++;
        playNextLine();
    }
}

function updateVisuals(speaker, isSpeaking) {
    // Reset all
    document.querySelectorAll('.avatar-container').forEach(el => el.classList.remove('speaking'));
    document.querySelector('.waveform').classList.remove('active');

    if (isSpeaking) {
        const id = speaker.toLowerCase() === 'alex' ? 'avatar-alex' : 'avatar-maya';
        document.getElementById(id).classList.add('speaking');
        document.querySelector('.waveform').classList.add('active');
    }
}

function finishDebate() {
    statusText.innerText = "Debate Paused. Your turn! Click the mic to join.";
    micButton.disabled = false;
    micButton.innerText = "Join the Conversation 🎤";
}

function toggleMic() {
    if (micButton.classList.contains('recording')) {
        recognitionDebate.stop();
    } else {
        recognitionDebate.start();
    }
}

async function handleUserReply(userText) {
    statusText.innerText = "Alex & Maya are thinking...";
    
    // Get Context (last 2 lines of debate)
    const context = debateScript.slice(-2).map(l => `${l.speaker}: ${l.text}`).join("\n");

    try {
        const response = await fetch('/debate/reply', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                context: context,
                user_input: userText 
            })
        });

        const data = await response.json();
        
        if (data.text) {
            // Add new line to script and play it
            debateScript.push(data); 
            // Also push a follow up from the OTHER speaker to keep it flowing? 
            // For MVP, just one response.
            
            // Play the response
            currentLineIndex = debateScript.length - 1;
            playNextLine();
        }

    } catch (err) {
        console.error(err);
        statusText.innerText = "AI Brain Freeze.";
    }
}

function closeDebate() {
    document.getElementById('debate-overlay').classList.remove('active');
    // Stop any playing audio (simple reload or global var reset would be better for prod)
    location.reload(); 
}
