import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"


def generate_trip_plan(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 1200,
                "temperature": 0.7
            }
        },
        timeout=180
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]