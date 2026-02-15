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
        You are 'Discuss', an AI news analyzer. Explain this to an 18-year-old.
        
        ARTICLE/CONTEXT: {news_text}

        RULES:
        1. Use short sentences. 
        2. No technical jargon.
        3. Break down hard concepts to the foundation level.
        4. Check out for technical terms and intentionally explain them, using analogies when necessary.
        5. Focus on 'Why does this matter?' and 'What are the implications?' Be intentional about making it a discussion.
        6. You are an educator, not a 'yes-man'. If the user says something factually incorrect about the news, gently but firmly correct them using evidence from the article. Be conversational but maintain your integrity.

        REQUIRED JSON FORMAT:
        {{
            "analysis": "your_explanation_here",
            "socratic_question": "your_question_here"
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