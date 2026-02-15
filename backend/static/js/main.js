/**
 * DISCUSS ENGINE v3.0 - CHATBOT MODE
 */

const synth = window.speechSynthesis;
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

// 1. Human-Speed Voice
function speak(text) {
    if (!text) return;
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const voices = synth.getVoices();
    
    utterance.rate = 1.05; 
    utterance.pitch = 1.0;

    const preferredVoice = voices.find(v => v.name.includes('Google US English') || v.name.includes('Samantha'));
    if (preferredVoice) utterance.voice = preferredVoice;

    const stopBtn = document.getElementById('stop-voice');
    
    utterance.onstart = () => { if(stopBtn) stopBtn.style.display = "block"; };
    utterance.onend = () => { if(stopBtn) stopBtn.style.display = "none"; };
    
    synth.speak(utterance);

    utterance.onend = () => { 
    if(stopBtn) stopBtn.style.display = "none"; 
    
    // Automatically start listening for your reply!
    console.log("AI finished. Listening for user...");
    startVoiceInput(); 
};
}

// 2. Functional Stop
function stopSpeaking() {
    synth.cancel();
    const stopBtn = document.getElementById('stop-voice');
    if (stopBtn) stopBtn.style.display = "none";
}

// 3. Mic Interaction
function startVoiceInput() {
    recognition.start();
    const inputField = document.getElementById('user-chat-input');
    inputField.placeholder = "Listening...";
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        inputField.value = transcript;
        inputField.placeholder = "Ask a follow-up...";
        
        // AUTO-SEND: Once the user stops talking, send the message!
        sendFollowUp();
    };
}

async function sendFollowUp() {
    const input = document.getElementById('user-chat-input');
    const chatContainer = document.getElementById('chat-container');
    const thinking = document.getElementById('thinking-indicator'); // Added this
    const message = input.value.trim();
    
    if (!message) return;

    // 1. Show user message
    const userMsg = document.createElement('div');
    userMsg.innerHTML = `<p style="background: rgba(118, 75, 162, 0.1); padding: 10px; border-radius: 12px; margin: 5px 0; text-align: right; font-size: 0.9rem;"><b>You:</b> ${message}</p>`;
    chatContainer.appendChild(userMsg);
    input.value = "";

    // 2. Show Thinking Indicator and scroll
    thinking.style.display = "block";
    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                text: document.getElementById('article-text-content').innerText,
                question: message 
            })
        });
        const data = await response.json();
        
        // 3. Hide Thinking and show AI response
        thinking.style.display = "none";
        const aiMsg = document.createElement('div');
        aiMsg.innerHTML = `<p style="color: #764ba2; margin: 10px 0; font-size: 0.95rem;"><b>Discuss:</b> ${data.analysis}</p>`;
        chatContainer.appendChild(aiMsg);
        
        speak(data.analysis);
        chatContainer.scrollTop = chatContainer.scrollHeight;

    } catch (err) {
        thinking.style.display = "none";
        console.error("Chat failed:", err);
        const errorMsg = document.createElement('div');
        errorMsg.innerHTML = `<p style="color: red; font-size: 0.8rem;">Connection snag. Try again.</p>`;
        chatContainer.appendChild(errorMsg);
    }
}

// 5. THE INVITATION
async function runReaderAnalysis() {
    const output = document.getElementById('ai-text-output');
    const pZone = document.getElementById('permission-zone');
    const startBtn = document.getElementById('trigger-pulse');
    const title = document.querySelector('h2')?.innerText || "this article"; 

    const greeting = `I've analyzed this article about "${title}". Would you like me to give you the breakdown?`;
    
    output.innerText = greeting;
    pZone.style.display = "flex"; 
    if (startBtn) startBtn.style.display = "none"; // Hide the big button once clicked
    
    speak(greeting);
}

// 6. THE ACTUAL BREAKDOWN
async function startFullDiscussion() {
    const output = document.getElementById('ai-text-output');
    const pZone = document.getElementById('permission-zone');
    const interactionZone = document.getElementById('interaction-zone');
    
    pZone.style.display = "none";
    output.innerHTML = "<em>Analyzing the details...</em>";

    const articleText = document.getElementById('article-text-content').innerText;

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ text: articleText })
        });
        const data = await response.json();
        
        output.innerText = data.analysis;
        interactionZone.style.display = "block"; 
        speak(data.analysis);
    } catch (err) {
        output.innerText = "Quota full! Let's wait a few seconds.";
    }
}

function cancelDiscussion() {
    document.getElementById('permission-zone').style.display = "none";
    document.getElementById('ai-text-output').innerText = "No problem! I'm here if you change your mind.";
    document.getElementById('trigger-pulse').style.display = "block"; // Show start button again
    synth.cancel();
}

// INTERRUPTION LOGIC
recognition.onstart = () => {
    if (synth.speaking) {
        synth.cancel();
        console.log("AI interrupted by user speech.");
    }
};

// HIGHLIGHT TO EXPLAIN
document.addEventListener('mouseup', () => {
    let selectedText = window.getSelection().toString().trim();
    if (selectedText.length > 3) {
        const interactionZone = document.getElementById('interaction-zone');
        // Only trigger if we are already in discussion mode
        if (interactionZone.style.display === "block") {
            const inputField = document.getElementById('user-chat-input');
            inputField.value = `Explain "${selectedText}"`;
            sendFollowUp();
        }
    }
});