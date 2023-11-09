from youtube_transcript_api import YouTubeTranscriptApi

from flask import Flask
import bleach
from youtube_transcript_api import YouTubeTranscriptApi

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Initialize Flask app
app = Flask(__name__)

# Initialize Limiter
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])
#OPEN AI initialization

@app.route('/get_video_transcript', methods=['POST'])
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
