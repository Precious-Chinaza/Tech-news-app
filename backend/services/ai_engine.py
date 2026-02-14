import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

class StartupMentor:
    def __init__(self):
        # Using the new Google GenAI SDK and Gemini 3 Flash
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_id = "gemini-3-flash-preview"

    def get_analysis(self, news_text):
        prompt = f"""
        "You are an AI mentor for 'Discuss'. Explain the following article to a 15-year-old student. Use detailed sentences. Avoid 'corporate' or 'technical' words. If you use a complex term, explain it with a funny analogy immediately. If you see a complex term or phrase in the article, explain it in simple terms. Focus on the 'Why does this matter?'"
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            
            # Clean the response in case the model adds markdown backticks
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except Exception as e:
            print(f"AI Error: {e}")
            return {
                "analysis": "I'm processing the latest market shifts. Give me a moment to recalibrate.",
                "socratic_question": "How would this news affect your burn rate?"
            }