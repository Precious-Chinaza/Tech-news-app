import os
import json
import re 
import requests
from google import genai
from dotenv import load_dotenv

load_dotenv()

class StartupMentor:
    def __init__(self):
        # Using the new Google GenAI SDK and Gemini 3 Flash
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_id = "gemini-3-flash-preview"
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        # Voice IDs (Defaults)
        self.voice_alex = "pNInz6obpgDQGcFmaJgB" # Adam (Male, Deep)
        self.voice_maya = "21m00Tcm4TlvDq8ikWAM" # Rachel (Female, Clear)

    def get_analysis(self, news_text):
        # We MUST pass the news_text into the prompt
        prompt = f"""
        You are 'Discuss', a tech-savvy friend sharing a quick update.
        Adopt a first-person perspective ("I just saw...", "It's wild that...").
        
        ARTICLE/CONTEXT: {news_text}

        RULES:
        1. **Conciseness is Key**: Keep it SHORT and punchy. Max 6-7 sentences. No fluff.
        2. **Persona**: Use "I", "me". Be casual and direct.
        3. **Focus**: What's the core story and why should we care? 
        4. **Clarity**: Simple language. If it's technical, simplify it instantly.
        5. **Integrity**: Gently correct facts if needed.

        REQUIRED JSON FORMAT:
        {{
            "analysis": "your_concise_first_person_take",
            "socratic_question": "one_short_engaging_question"
        }}
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            text = response.text.strip()
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return json.loads(text)
            
        except Exception as e:
            error_msg = str(e)
            print(f"Detailed AI Error: {error_msg}")
            
            # Check if it's a Rate Limit error
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                return {
                    "analysis": "Phew! We're talking so fast I need to catch my breath for about 15 seconds. Give me a moment!",
                    "socratic_question": "Want to try again in a few seconds?"
                }
            
            return {
                "analysis": "I hit a snag reading this. Let's try re-analyzing!",
                "socratic_question": "Want me to try again?"
            }

    def generate_debate_script(self, news_text):
        prompt = f"""
        Generate a 'Roundtable Debate' script between two tech podcasters discussing this article.
        
        CHARACTERS:
        1. **Alex** (Male): Skeptical, cynical, focuses on privacy risks, hype cycles, and technical limitations.
        2. **Maya** (Female): Optimistic, visionary, focuses on innovation, future potential, and human benefit.

        ARTICLE/CONTEXT: {news_text}

        FORMAT:
        - A JSON list of objects.
        - Each object has "speaker" ("Alex" or "Maya") and "text" (their dialogue).
        - Keep it snappy! 4-6 exchanges total.
        - End with ONE of them asking the LISTENER (the user) a direct question to join the debate.
        
        EXAMPLE JSON:
        [
            {{"speaker": "Alex", "text": "I don't know, this seems like vaporware to me."}},
            {{"speaker": "Maya", "text": "You're always so negative! Think about the applications for healthcare."}},
            {{"speaker": "Alex", "text": "But what about the data privacy? Who owns that data?"}},
            {{"speaker": "Maya", "text": "That's a fair point. Hey listener, would you trust this tech with your data?"}}
        ]
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            
            text = response.text.strip()
            # Clean up potential markdown code blocks
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
                
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return json.loads(text)
            
        except Exception as e:
            print(f"Debate Script Error: {e}")
            return []

    def generate_audio(self, text, speaker):
        if not self.elevenlabs_api_key:
            print("!!! ELEVENLABS API KEY MISSING FROM ENV !!!")
            return None
            
        voice_id = self.voice_alex if speaker == "Alex" else self.voice_maya
        print(f"--- Generating Audio for {speaker} using voice {voice_id} ---")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.8,      # Increased for more consistency
                "similarity_boost": 0.8, # Increased for better character matching
                "style": 0.5,
                "use_speaker_boost": True
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                print(f"--- Audio Successfully Generated ({len(response.content)} bytes) ---")
                return response.content
            else:
                print(f"!!! ELEVENLABS API ERROR: {response.status_code} - {response.text} !!!")
                return None
        except Exception as e:
            print(f"!!! CRITICAL AUDIO GEN ERROR: {e} !!!")
            return None

    def generate_debate_response(self, context_text, user_input):
        prompt = f"""
        You are roleplaying as Alex (Skeptic) and Maya (Optimist) in a live podcast.
        
        CONTEXT: The user just joined the conversation.
        PREVIOUS DISCUSSION TOPIC: {context_text}
        USER SAID: "{user_input}"
        
        TASK:
        Generate a response from EITHER Alex OR Maya (whoever would naturally respond best).
        - If the user agrees with Maya, Alex should challenge them.
        - If the user agrees with Alex, Maya should offer a counterpoint.
        - Keep it short (1-2 sentences).
        
        JSON FORMAT:
        {{
            "speaker": "Name",
            "text": "Response text"
        }}
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            text = response.text.strip()
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return json.loads(text)
        except Exception as e:
            print(f"Debate Response Error: {e}")
            return {"speaker": "Maya", "text": "That's an interesting perspective! Thanks for sharing."}
