from flask import Flask
import bleach
from youtube_transcript_api import YouTubeTranscriptApi
import os
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from youtube_transcript_api import YouTubeTranscriptApi
import re
from functools import wraps  
import os
from dotenv import load_dotenv
# Initialize Flask app
app = Flask(__name__)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path, verbose=True)

def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        api_keys = os.environ.get('API_KEYS')
        
        # Check if API keys are loaded
        if api_keys is None:
            raise EnvironmentError("API keys not loaded. Ensure your .env file is configured correctly.")
        
        api_keys_list = api_keys.split(',')
        auth_header = request.headers.get('Authorization')
        
        if auth_header and any(f'Bearer {key}' == auth_header for key in api_keys_list):
            return view_function(*args, **kwargs)
        else:
            return jsonify(error="Invalid API key"), 401
    return decorated_function


# Initialize Limiter
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])
#OPEN AI initialization

@app.route('/get_video_transcript', methods=['POST'])
@require_api_key
@limiter.limit("30 per minute")
def get_video_transcript():
    content = request.json
    video_url = content.get('video_url', '')

    # Input validation for YouTube URL or ID
    if not re.match(r'^(https:\/\/www\.youtube\.com\/watch\?v=)?[a-zA-Z0-9_-]{11}', video_url):
        return jsonify({"error": "Invalid YouTube URL or ID"}), 400



    video_id = extract_video_id(video_url)

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return jsonify({"transcript": " ".join([d['text'] for d in transcript])})
    except Exception as e:

        return jsonify({"error": "Could not find a transcript for this video"}), 404

def extract_video_id(url_or_id):
    if "www.youtube.com/watch?v=" in url_or_id:
        return url_or_id.split('=')[1].split('&')[0]
    return url_or_id

@app.route('/health', methods=['GET'])
@require_api_key
def health_check():
    return jsonify(status="UP"), 200

def sanitize_text(text):
  # define the allowed HTML tags, attributes and styles
  allowed_tags = ["b", "i", "u", "a", "p", "br"]
  allowed_attrs = {"a": ["href", "title"]}
  # clean the input text using bleach
  clean_text = bleach.clean(text, tags=allowed_tags, attributes=allowed_attrs)
  # return the sanitized text
  return clean_text

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
