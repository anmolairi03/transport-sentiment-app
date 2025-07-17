from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
load_dotenv()
from database import db
from collections import defaultdict
import datetime

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
        return "bus"  # default fallback

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
    return region

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
        if tweets:
            return jsonify({
                'status': 'API is running!',
                'database': 'connected',
                'total_tweets': len(db.get_recent_tweets(limit=1000))
            })
        else:
            return jsonify({
                'status': 'API is running!',
                'database': 'disconnected',
                'total_tweets': 0
            }), 500
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
            sentiment_label = row['sentiment'] if 'sentiment' in row else 'neutral'
            transport_type = determine_transport_type(row['text'] if 'text' in row else '')
            region = row['region'] if 'region' in row else 'India'
            
            # Extract state and city from region
            if ',' in region:
                city, state = region.split(',', 1)
                city = city.strip()
                state = state.strip()
            else:
                state = region
                city = region
            
            tweets.append({
                "id": row['id'],
                "text": row['text'],
                "timestamp": row['created_at'].isoformat() if 'created_at' in row and row['created_at'] else datetime.datetime.now().isoformat(),
                "location": region,
                "state": state,
                "city": city,
                "transportType": transport_type,
                "sentiment": {
                    "polarity": determine_sentiment_score(sentiment_label),
                    "label": sentiment_label,
                    "confidence": 0.85  # dummy value, can be enhanced
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

        # Group by state
        state_data = defaultdict(lambda: {
            'total_messages': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'transport_breakdown': {'bus': 0, 'metro': 0, 'train': 0, 'auto': 0, 'taxi': 0}
        })

        # Get all tweets for transport type analysis
        all_tweets = db.get_recent_tweets(limit=10000)
        
        for tweet in all_tweets:
            transport_type = determine_transport_type(tweet['text'])
            state = extract_state_from_region(tweet['region'])
            state_data[state]['transport_breakdown'][transport_type] += 1

        states_data = []
        for row in rows:
            region = row['region']
            state = extract_state_from_region(region)
            
            # Aggregate data by state
            state_info = state_data[state]
            state_info['total_messages'] += row['total_messages']
            state_info['positive_count'] += row['positive_count']
            state_info['negative_count'] += row['negative_count']
            state_info['neutral_count'] += row['neutral_count']

        # Convert to final format
        for state, data in state_data.items():
            if data['total_messages'] > 0:
                sentiment_score = (data['positive_count'] - data['negative_count']) / data['total_messages']
                
                states_data.append({
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

        return jsonify(states_data)

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# --- Run Server ---
if __name__ == '__main__':
    print("🚀 Starting Indian Transport Sentiment API...")
    print("📊 Serving data for all Indian states")
    app.run(host='0.0.0.0', port=PORT, debug=True)
