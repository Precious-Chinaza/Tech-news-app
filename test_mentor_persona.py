import os
import sys
# Add backend to sys path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from dotenv import load_dotenv
from google import genai
from services.ai_engine import StartupMentor

# 1. Load the key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: No GEMINI_API_KEY found in your .env file!")
else:
    # 2. Setup the Mentor
    mentor = StartupMentor()

    print("🧪 Testing Startup Mentor Persona (Gemini 3 Flash)...")
    test_text = "SpaceX just successfully launched another batch of Starlink satellites, aiming to bring internet to remote areas globally. However, astronomers are concerned about light pollution affecting their observations."

    try:
        # 3. Get Analysis
        analysis = mentor.get_analysis(test_text)
        print("\n✅ SUCCESS! Mentor says:\n")
        print(f"Analysis: {analysis['analysis']}")
        print(f"\nQuestion: {analysis['socratic_question']}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")