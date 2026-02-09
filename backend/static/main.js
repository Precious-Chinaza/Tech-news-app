// This function triggers when a user clicks "Learn with Mentor"
async function analyzeArticle(articleId) {
    const articleElement = document.getElementById(`article-text-${articleId}`);
    const textToAnalyze = articleElement.innerText;
    
    // UI Feedback: Show a loading state
    const mentorPanel = document.getElementById('mentor-display');
    mentorPanel.innerHTML = "<p class='loading'>Consulting the Startup Mentor...</p>";

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: textToAnalyze })
        });

        const data = await response.json();

        // Layer 2: Displaying the AI's "Thinking Style"
        renderMentorAnalysis(data);
    } catch (error) {
        console.error("Analysis failed:", error);
        mentorPanel.innerHTML = "<p class='error'>The Mentor is offline. Check your API key.</p>";
    }
}

function renderMentorAnalysis(data) {
    const mentorPanel = document.getElementById('mentor-display');
    
    // We use the JSON keys defined in our ai_engine.py
    mentorPanel.innerHTML = `
        <div class="mentor-box">
            <h3>🎓 Startup Mentor Insights</h3>
            <p>${data.analysis}</p>
            <hr>
            <div class="socratic-zone">
                <p><strong>Question:</strong> ${data.socratic_question}</p>
                <input type="text" id="user-answer" placeholder="Type your thoughts...">
                <button onclick="checkAnswer()">Submit Response</button>
            </div>
        </div>
    `;
}

async function checkAnswer() {
    const userAnswer = document.getElementById('user-answer').value;
    const mentorDisplay = document.getElementById('mentor-display');
    
    if (!userAnswer) {
        alert("The Mentor wants to hear your thoughts first!");
        return;
    }

    // UI Feedback
    const submitBtn = document.querySelector('.socratic-zone button');
    submitBtn.innerText = "Evaluating...";
    submitBtn.disabled = true;

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // We tell the AI this is a FOLLOW-UP answer to a question
            body: JSON.stringify({ 
                text: `The user was asked a question. Their answer is: "${userAnswer}". Evaluate if they understood the business/tech concept and provide a brief encouraging feedback or correction.` 
            })
        });

        const data = await response.json();
        
        // Append the feedback to the panel
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'mentor-feedback';
        feedbackDiv.innerHTML = `
            <p style="color: #764ba2; font-weight: bold; margin-top: 15px;">Mentor's Feedback:</p>
            <p>${data.analysis}</p>
        `;
        mentorDisplay.appendChild(feedbackDiv);
        
        submitBtn.innerText = "Discussion Complete";
    } catch (error) {
        console.error("Feedback failed:", error);
    }
}

// Utility to open/close the panel
function toggleMentor() {
    const panel = document.getElementById('mentor-panel');
    panel.classList.toggle('active');
}