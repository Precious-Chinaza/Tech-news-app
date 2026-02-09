import os
from dotenv import load_dotenv
from google import genai

# 1. Load the key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ ERROR: No GEMINI_API_KEY found in your .env file!")
else:
    # 2. Setup the Client
    client = genai.Client(api_key=api_key)

    print("🧪 Testing Startup Mentor Engine (Gemini 3 Flash)...")
    test_text = "Nvidia reports record earnings due to AI chip demand."

    try:
        # 3. Using the EXACT model ID from your list
        response = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=f"You are the Startup Mentor. Explain the business strategy of this news in 2 sentences: {test_text}"
        )
        print("\n✅ SUCCESS! Mentor says:")
        print(response.text)
    except Exception as e:
        print(f"\n❌ STILL AN ERROR: {e}")