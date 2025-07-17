from dotenv import load_dotenv
load_dotenv()

from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import datetime
from collections import defaultdict

from database import db

app = Flask(__name__)
CORS(app)

# Get port from environment variable (Render sets this)
PORT = int(os.environ.get('PORT', 5000))

# --- Helper Functions ---
def determine_transport_type(text):
    """Enhanced transport type detection"""
    text = text.lower()
    if any(keyword in text for keyword in ['metro', 'मेट्रो', 'subway', 'dmrc']):
        return "metro"
    elif any(keyword in text for keyword in ['train', 'ट्रेन', 'railway', 'irctc', 'local train']):
        return "train"
    elif any(keyword in text for keyword in ['auto', 'ऑटो', 'rickshaw', 'three wheeler']):
        return "auto"
    elif any(keyword in text for keyword in ['taxi', 'टैक्सी', 'cab', 'ola', 'uber']):
        return "taxi"
    else:
        return "bus"  # fallback

def determine_sentiment_score(label):
    return {
        'positive': 0.5,
        'negative': -0.5,
        'neutral': 0
    }.get(label.lower(), 0)

def extract_state_from_region(region):
    """Extract state name from region field"""
    if ',' in region:
        return region.split(',')[-1].strip()
    return region.strip()

# --- Routes ---

@app.route('/api/health')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        'status': 'healthy',
        'service': 'transport-sentiment-api',
        'database': 'connected' if db.connection else 'disconnected'
    })

@app.route('/api/status')
def status():
    """API health check"""
    try:
        tweets = db.get_recent_tweets(limit=1)
        return jsonify({
            'status': 'API is running!',
            'database': 'connected' if tweets else 'no data',
            'total_tweets': len(db.get_recent_tweets(limit=1000))
        })
    except Exception as e:
        return jsonify({
            'status': 'API is running!',
            'database': 'error',
            'error': str(e)
        }), 500

@app.route('/api/tweets')
def get_tweets():
    """Get recent tweets with sentiment analysis"""
    try:
        rows = db.get_recent_tweets(limit=100)
        tweets = []

        for row in rows:
            text = row.get('text', '')
            region = row.get('region', 'India')
            sentiment_label = row.get('sentiment', 'neutral')
            created_at = row.get('created_at', datetime.datetime.now())

            transport_type = determine_transport_type(text)

            if ',' in region:
                city, state = [part.strip() for part in region.split(',', 1)]
            else:
                city = state = region.strip()

            tweets.append({
                "id": row.get('id'),
                "text": text,
                "timestamp": created_at.isoformat(),
                "location": region,
                "state": state,
                "city": city,
                "transportType": transport_type,
                "sentiment": {
                    "polarity": determine_sentiment_score(sentiment_label),
                    "label": sentiment_label,
                    "confidence": 0.85  # can be updated if model provides it
                }
            })

        return jsonify(tweets)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/states')
def get_states_summary():
    """Get aggregated sentiment data by state"""
    try:
        rows = db.get_state_summary()
        all_tweets = db.get_recent_tweets(limit=10000)

        # Transport breakdown placeholder
        state_data = defaultdict(lambda: {
            'total_messages': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'transport_breakdown': {'bus': 0, 'metro': 0, 'train': 0, 'auto': 0, 'taxi': 0}
        })

        for tweet in all_tweets:
            state = extract_state_from_region(tweet.get('region', 'Unknown'))
            transport = determine_transport_type(tweet.get('text', ''))
            state_data[state]['transport_breakdown'][transport] += 1

        for row in rows:
            state = extract_state_from_region(row.get('region', 'Unknown'))
            state_data[state]['total_messages'] += row.get('total_messages', 0)
            state_data[state]['positive_count'] += row.get('positive_count', 0)
            state_data[state]['negative_count'] += row.get('negative_count', 0)
            state_data[state]['neutral_count'] += row.get('neutral_count', 0)

        result = []
        for state, data in state_data.items():
            if data['total_messages'] > 0:
                sentiment_score = (data['positive_count'] - data['negative_count']) / data['total_messages']
                result.append({
                    "state": state,
                    "sentimentScore": sentiment_score,
                    "totalMessages": data['total_messages'],
                    "transportBreakdown": data['transport_breakdown'],
                    "sentimentBreakdown": {
                        "positive": data['positive_count'],
                        "negative": data['negative_count'],
                        "neutral": data['neutral_count']
                    }
                })

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# --- Run Server ---
if __name__ == '__main__':
    print("🚀 Starting Indian Transport Sentiment API...")
    print("📊 Serving data for all Indian states")
    app.run(host='0.0.0.0', port=PORT, debug=True)
