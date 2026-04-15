
import requests
import json
from config import settings

class LLMClient:
    def __init__(self):
        self.endpoint = f"{settings.LLM_ENDPOINT}/chat/completions"
        self.api_key = settings.LLM_API_KEY

    def generate_response(self, prompt, system_prompt="You are a helpful coding assistant."):
        payload = {
            "model": "local-model", # LM Studio typically ignores this or uses the loaded model
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": settings.LLM_MAX_TOKENS
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if settings.LLM_DEBUG_LOGGING:
            print(f"[LLM Request] Prompt: {prompt[:100]}...")

        try:
            response = requests.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            if settings.LLM_DEBUG_LOGGING:
                print(f"[LLM Response] Content: {content[:100]}...")
                
            return content
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return f"Error occurred while contacting the LLM: {str(e)}"
