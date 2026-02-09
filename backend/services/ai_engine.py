import os
import google.generativeai as genai
import json

class StartupMentor:
    def __init__(self):
        # Configure Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        self.system_prompt = (
            "You are the 'Startup Mentor'. Explain tech news to developers. "
            "Focus on business, money, and policy. Break it down simply. "
            "Output MUST be in valid JSON format with keys: 'analysis' and 'socratic_question'."
        )

    def analyze_content(self, article_text):
        try:
            # Combine prompt and content
            full_prompt = f"{self.system_prompt}\n\nAnalyze this news description: {article_text}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            
            return response.text
        except Exception as e:
            return json.dumps({"error": str(e), "analysis": "The Mentor is busy. Try again!", "socratic_question": ""})