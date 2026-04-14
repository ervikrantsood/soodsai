from google import genai
from config import GEMINI_API_KEYS
from dotenv import load_dotenv

load_dotenv()

def list_my_models():
    valid_keys = [k for k in GEMINI_API_KEYS if k and k.strip()]
    if not valid_keys:
        print("No API Keys found.")
        return

    for i, api_key in enumerate(valid_keys):
        print(f"\n--- Testing Key {i+1} : {api_key[:6]}...{api_key[-5:]} ---")
        client = genai.Client(api_key=api_key)
        try:
            models = client.models.list()
            print(f"[SUCCESS] Found {len(list(models))} models available.")
        except Exception as e:
            print(f"[ERROR] with this key: {e}")

if __name__ == "__main__":
    list_my_models()
