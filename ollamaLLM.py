import requests

class OllamaLLM:
    def __init__(self, base_url='http://localhost:11434/api/generate'):
        self.base_url = base_url

    def generate_response(self, prompt, model='llama3dolphin-llama3:8b', stream=False): #use llama3 or minstral for other tasks
        data = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        response = requests.post(self.base_url, json=data)
        if response.status_code == 200:
            return response.json()['response']
        else:
            raise Exception(f"Failed to generate response with status code {response.status_code}: {response.text}")

    def bind(self, stop=None):
        # Dummy bind method to satisfy the Agent class requirements
        return self

# Example usage
# api = OllamaAPI()
# try:
#     result = api.generate_response("Tell me about the latest news in technology.")
#     print(result)
# except Exception as e:
#     print(e)
