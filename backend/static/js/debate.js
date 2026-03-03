// Debate Roundtable Engine

let debateScript = [];
let currentLineIndex = 0;
let isDebateActive = false;
let audioCache = {}; // Cache audio blobs to prevent re-fetching
let isPlaying = false;
let recognitionDebate;
let isUserTurn = false;

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
        micButton.innerText = "Recording... 🎤";
    };

    recognitionDebate.onend = () => {
        micButton.classList.remove('recording');
        if (isUserTurn) {
            micButton.innerText = "Join the Conversation 🎤";
        }
    };

    recognitionDebate.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        statusText.innerText = `You said: "${transcript}"`;
        handleUserReply(transcript);
    };
    
    recognitionDebate.onerror = (event) => {
        console.error("Speech Error:", event.error);
        statusText.innerText = "Mic error. Try again.";
    };
}

async function startDebate() {
    const articleText = document.getElementById('article-text-content').innerText;
    const articleUrl = new URLSearchParams(window.location.search).get('url');
    
    // Reset state
    debateScript = [];
    currentLineIndex = 0;
    isUserTurn = false;
    micButton.disabled = true;
    micButton.innerText = "Prepping... ⏳";
    
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
        
        if (data.script && data.script.length > 0) {
            debateScript = data.script;
            statusText.innerText = "Showtime! Starting debate...";
            // Start playback immediately
            playNextLine();
            
            // Pre-fetch next audio lines in background
            preloadAudio(1); 
        } else {
            statusText.innerText = "Error: Alex and Maya are speechless. Try again.";
        }
        
    } catch (err) {
        console.error(err);
        statusText.innerText = "Connection Error. Check your internet.";
    }
}

// Pre-fetch audio to make transitions smoother
async function preloadAudio(index) {
    if (index >= debateScript.length || audioCache[index]) return;
    
    const line = debateScript[index];
    try {
        const response = await fetch('/debate/audio', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ text: line.text, speaker: line.speaker })
        });
        if (response.ok) {
            const blob = await response.blob();
            audioCache[index] = URL.createObjectURL(blob);
        }
    } catch (e) {
        console.warn("Preload failed for index", index, e);
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
        let audioUrl = audioCache[currentLineIndex];
        
        if (!audioUrl) {
            // Not pre-loaded, fetch now
            const audioResponse = await fetch('/debate/audio', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ text: line.text, speaker: line.speaker })
            });

            if (!audioResponse.ok) throw new Error("Audio Failed");
            const blob = await audioResponse.blob();
            audioUrl = URL.createObjectURL(blob);
        }

        const audio = new Audio(audioUrl);
        
        audio.onplay = () => {
            // Preload the NEXT line while this one plays
            preloadAudio(currentLineIndex + 1);
        };

        audio.onended = () => {
            updateVisuals(line.speaker, false);
            currentLineIndex++;
            
            // Phase 2: Showtime - Natural Banter Interval
            const delay = currentLineIndex < debateScript.length ? 1200 : 500;
            statusText.innerText = "Brief pause...";
            setTimeout(playNextLine, delay);
        };

        await audio.play();

    } catch (err) {
        console.error("Playback error:", err);
        statusText.innerText = "Audio Error. Skipping...";
        currentLineIndex++;
        setTimeout(playNextLine, 500);
    }
}

function updateVisuals(speaker, isSpeaking) {
    document.querySelectorAll('.avatar-container').forEach(el => el.classList.remove('speaking'));
    document.querySelector('.waveform').classList.remove('active');

    if (isSpeaking) {
        const id = speaker.toLowerCase() === 'alex' ? 'avatar-alex' : 'avatar-maya';
        const avatar = document.getElementById(id);
        if (avatar) avatar.classList.add('speaking');
        document.querySelector('.waveform').classList.add('active');
    }
}

function finishDebate() {
    isUserTurn = true;
    statusText.innerText = "Maya asked you a question! Click the mic to reply.";
    micButton.disabled = false;
    micButton.innerText = "Join the Conversation 🎤";
    
    // Auto-activate mic for "Mic Drop" phase
    setTimeout(() => {
        if (isUserTurn && !micButton.classList.contains('recording')) {
            toggleMic();
        }
    }, 1000);
}

function toggleMic() {
    if (micButton.classList.contains('recording')) {
        recognitionDebate.stop();
    } else {
        recognitionDebate.start();
    }
}

async function handleUserReply(userText) {
    isUserTurn = false;
    micButton.disabled = true;
    micButton.innerText = "AI is thinking... 🧠";
    statusText.innerText = "Alex and Maya are reacting to your point...";
    
    // Phase 3: The Rebuttal Loop
    const context = debateScript.slice(-3).map(l => `${l.speaker}: ${l.text}`).join("\n");

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
        
        if (data.responses && Array.isArray(data.responses)) {
            // Append multiple responses for more natural banter
            const startIndex = debateScript.length;
            debateScript.push(...data.responses);
            
            // Clear cache for new lines
            currentLineIndex = startIndex;
            playNextLine();
        } else if (data.speaker && data.text) {
            const startIndex = debateScript.length;
            debateScript.push(data);
            currentLineIndex = startIndex;
            playNextLine();
        }

    } catch (err) {
        console.error("Rebuttal error:", err);
        statusText.innerText = "Connection snag. Try the mic again.";
        isUserTurn = true;
        micButton.disabled = false;
        micButton.innerText = "Join the Conversation 🎤";
    }
}

function closeDebate() {
    document.getElementById('debate-overlay').classList.remove('active');
    // Stop audio by pausing all audio elements
    const audios = document.querySelectorAll('audio');
    audios.forEach(a => a.pause());
    location.reload(); 
}
