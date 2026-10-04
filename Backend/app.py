import base64
import os
import tempfile
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai

load_dotenv()

app = Flask(__name__)
CORS(app)

# Retrieve API keys from environment variables
gemini_api_key = os.getenv("GEMINI_API")
murf_api_key = os.getenv("MURF_API_KEY")

client = genai.Client(api_key=gemini_api_key)

PROMPTS = {
    "Summary": """
        You are a professional tourist guide.
Provide a high-level overview of "{place}" in {language}.

Focus on:
- The historical significance
- Why the place is famous
- Key architectural or cultural highlights

Keep the explanation concise, engaging, and easy to follow.
Avoid excessive details and dates.
Limit the response to around 200 words.

Respond ONLY in {language}.
    """,
    "Detailed": """
        You are a professional tourist guide.
Provide a detailed and immersive explanation of "{place}" in {language}.

Cover:
- Historical background and timeline
- Architectural design and unique features
- Cultural importance and notable events
- Interesting facts and visitor insights

Explain concepts clearly and in a storytelling manner.
Include relevant details and examples to create a rich experience.
Limit the response to around 400 words.

Respond ONLY in {language}.
    """
}


def generate_description(place, answer_type, language):
    prompt = PROMPTS[answer_type].format(place=place, language=language)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


def generate_speech(text, voice_id, locale):
    url = "https://global.api.murf.ai/v1/speech/stream"

    headers = {
        "api-key": murf_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "voiceId": voice_id,
        "locale": locale,
        "format": "MP3",
    }

    response = requests.post(url, json=payload, headers=headers)

    # Save audio to a temporary file
    temp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    temp_audio.write(response.content)
    temp_audio.close()

    return temp_audio.name


@app.route("/generate-audio-guide", methods=["POST"])
def generate_audio_guide():
    data = request.json
    place = data["place"]
    answer_type = data["answerType"]
    language = data["language"]
    voice_id = data["voiceId"]
    locale = data["locale"]

    description = generate_description(place, answer_type, language)
    audio_path = generate_speech(description, voice_id, locale)

    with open(audio_path, "rb") as audio_file:
        audio_base64 = base64.b64encode(audio_file.read()).decode("utf-8")

    # Clean up the temporary file after reading
    if os.path.exists(audio_path):
        os.remove(audio_path)

    return jsonify({
        "description": description,
        "audio": audio_base64,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)