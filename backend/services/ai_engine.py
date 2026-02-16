import os
import json
import re 
from google import genai
from dotenv import load_dotenv

load_dotenv()

class StartupMentor:
    def __init__(self):
        # Using the new Google GenAI SDK and Gemini 3 Flash
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_id = "gemini-3-flash-preview"

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