import json
import mysql.connector
from textblob import TextBlob
import emoji
import os
import re

# ---------- DATABASE CONFIG ----------
DB_CONFIG = {
    "host": os.getenv('MYSQL_HOST', 'localhost'),
    "user": os.getenv('MYSQL_USER', 'root'),
    "password": os.getenv('MYSQL_PASSWORD', 'gadheullu12'),
    "database": os.getenv('MYSQL_DATABASE', 'transport_sentiment_app'),
    "port": int(os.getenv('MYSQL_PORT', 3306)),
    "charset": "utf8mb4",
    "collation": "utf8mb4_unicode_ci"
}

# ---------- INDIAN STATES AND CITIES MAPPING ----------
INDIAN_STATES_CITIES = {
    'Andhra Pradesh': ['Visakhapatnam', 'Vijayawada', 'Guntur', 'Nellore', 'Kurnool', 'Rajahmundry', 'Tirupati'],
    'Arunachal Pradesh': ['Itanagar', 'Naharlagun', 'Pasighat', 'Tezpur'],
    'Assam': ['Guwahati', 'Silchar', 'Dibrugarh', 'Jorhat', 'Nagaon', 'Tinsukia'],
    'Bihar': ['Patna', 'Gaya', 'Bhagalpur', 'Muzaffarpur', 'Darbhanga', 'Bihar Sharif'],
    'Chhattisgarh': ['Raipur', 'Bhilai', 'Korba', 'Bilaspur', 'Durg', 'Rajnandgaon'],
    'Goa': ['Panaji', 'Margao', 'Vasco da Gama', 'Mapusa', 'Ponda'],
    'Gujarat': ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Bhavnagar', 'Jamnagar'],
    'Haryana': ['Gurgaon', 'Faridabad', 'Panipat', 'Ambala', 'Yamunanagar', 'Rohtak'],
    'Himachal Pradesh': ['Shimla', 'Dharamshala', 'Solan', 'Mandi', 'Kullu', 'Hamirpur'],
    'Jharkhand': ['Ranchi', 'Jamshedpur', 'Dhanbad', 'Bokaro', 'Deoghar', 'Hazaribagh'],
    'Karnataka': ['Bangalore', 'Mysore', 'Hubli', 'Mangalore', 'Belgaum', 'Gulbarga'],
    'Kerala': ['Kochi', 'Thiruvananthapuram', 'Kozhikode', 'Thrissur', 'Kollam', 'Palakkad'],
    'Madhya Pradesh': ['Bhopal', 'Indore', 'Gwalior', 'Jabalpur', 'Ujjain', 'Sagar'],
    'Maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Nashik', 'Aurangabad', 'Solapur'],
    'Manipur': ['Imphal', 'Thoubal', 'Bishnupur', 'Churachandpur'],
    'Meghalaya': ['Shillong', 'Tura', 'Jowai', 'Nongstoin'],
    'Mizoram': ['Aizawl', 'Lunglei', 'Saiha', 'Champhai'],
    'Nagaland': ['Kohima', 'Dimapur', 'Mokokchung', 'Tuensang'],
    'Odisha': ['Bhubaneswar', 'Cuttack', 'Rourkela', 'Berhampur', 'Sambalpur', 'Puri'],
    'Punjab': ['Chandigarh', 'Ludhiana', 'Amritsar', 'Jalandhar', 'Patiala', 'Bathinda'],
    'Rajasthan': ['Jaipur', 'Jodhpur', 'Udaipur', 'Kota', 'Bikaner', 'Ajmer'],
    'Sikkim': ['Gangtok', 'Namchi', 'Gyalshing', 'Mangan'],
    'Tamil Nadu': ['Chennai', 'Coimbatore', 'Madurai', 'Salem', 'Tiruchirappalli', 'Tirunelveli'],
    'Telangana': ['Hyderabad', 'Warangal', 'Nizamabad', 'Karimnagar', 'Khammam', 'Mahbubnagar'],
    'Tripura': ['Agartala', 'Dharmanagar', 'Udaipur', 'Kailashahar'],
    'Uttar Pradesh': ['Lucknow', 'Kanpur', 'Agra', 'Varanasi', 'Meerut', 'Allahabad'],
    'Uttarakhand': ['Dehradun', 'Haridwar', 'Roorkee', 'Haldwani', 'Rudrapur', 'Kashipur'],
    'West Bengal': ['Kolkata', 'Howrah', 'Durgapur', 'Siliguri', 'Asansol', 'Malda'],
    'Delhi': ['New Delhi', 'Gurgaon', 'Noida', 'Faridabad', 'Ghaziabad'],
    'Jammu and Kashmir': ['Srinagar', 'Jammu', 'Anantnag', 'Baramulla', 'Udhampur'],
    'Ladakh': ['Leh', 'Kargil', 'Nubra', 'Zanskar']
}

# ---------- REGION DETECTION FUNCTION ----------
def detect_region_from_text(text):
    """
    Detect region (state or major city) from tweet text
    """
    text_lower = text.lower()
    
    # Check for direct state mentions
    for state, cities in INDIAN_STATES_CITIES.items():
        if state.lower() in text_lower:
            return state
    
    # Check for city mentions and return the state
    for state, cities in INDIAN_STATES_CITIES.items():
        for city in cities:
            if city.lower() in text_lower:
                return f"{city}, {state}"
    
    # Check for common abbreviations and nicknames
    location_mappings = {
        'mumbai': 'Mumbai, Maharashtra',
        'delhi': 'Delhi',
        'bangalore': 'Bangalore, Karnataka',
        'bengaluru': 'Bangalore, Karnataka',
        'chennai': 'Chennai, Tamil Nadu',
        'kolkata': 'Kolkata, West Bengal',
        'calcutta': 'Kolkata, West Bengal',
        'hyderabad': 'Hyderabad, Telangana',
        'pune': 'Pune, Maharashtra',
        'ahmedabad': 'Ahmedabad, Gujarat',
        'surat': 'Surat, Gujarat',
        'jaipur': 'Jaipur, Rajasthan',
        'lucknow': 'Lucknow, Uttar Pradesh',
        'kanpur': 'Kanpur, Uttar Pradesh',
        'nagpur': 'Nagpur, Maharashtra',
        'patna': 'Patna, Bihar',
        'indore': 'Indore, Madhya Pradesh',
        'bhopal': 'Bhopal, Madhya Pradesh',
        'ludhiana': 'Ludhiana, Punjab',
        'agra': 'Agra, Uttar Pradesh',
        'nashik': 'Nashik, Maharashtra',
        'vadodara': 'Vadodara, Gujarat',
        'gurgaon': 'Gurgaon, Haryana',
        'gurugram': 'Gurgaon, Haryana',
        'noida': 'Noida, Delhi',
        'faridabad': 'Faridabad, Haryana',
        'ghaziabad': 'Ghaziabad, Delhi',
        'rajkot': 'Rajkot, Gujarat',
        'kochi': 'Kochi, Kerala',
        'cochin': 'Kochi, Kerala',
        'coimbatore': 'Coimbatore, Tamil Nadu',
        'madurai': 'Madurai, Tamil Nadu',
        'jodhpur': 'Jodhpur, Rajasthan',
        'raipur': 'Raipur, Chhattisgarh',
        'kota': 'Kota, Rajasthan',
        'guwahati': 'Guwahati, Assam',
        'chandigarh': 'Chandigarh, Punjab',
        'thiruvananthapuram': 'Thiruvananthapuram, Kerala',
        'trivandrum': 'Thiruvananthapuram, Kerala',
        'mysore': 'Mysore, Karnataka',
        'mysuru': 'Mysore, Karnataka',
        'salem': 'Salem, Tamil Nadu',
        'meerut': 'Meerut, Uttar Pradesh',
        'jabalpur': 'Jabalpur, Madhya Pradesh',
        'gwalior': 'Gwalior, Madhya Pradesh',
        'vijayawada': 'Vijayawada, Andhra Pradesh',
        'visakhapatnam': 'Visakhapatnam, Andhra Pradesh',
        'vizag': 'Visakhapatnam, Andhra Pradesh',
        'ranchi': 'Ranchi, Jharkhand',
        'jamshedpur': 'Jamshedpur, Jharkhand',
        'dhanbad': 'Dhanbad, Jharkhand',
        'amritsar': 'Amritsar, Punjab',
        'jalandhar': 'Jalandhar, Punjab',
        'allahabad': 'Allahabad, Uttar Pradesh',
        'prayagraj': 'Allahabad, Uttar Pradesh',
        'varanasi': 'Varanasi, Uttar Pradesh',
        'banaras': 'Varanasi, Uttar Pradesh',
        'howrah': 'Howrah, West Bengal',
        'durgapur': 'Durgapur, West Bengal',
        'siliguri': 'Siliguri, West Bengal',
        'asansol': 'Asansol, West Bengal'
    }
    
    for keyword, region in location_mappings.items():
        if keyword in text_lower:
            return region
    
    # Default fallback
    return 'India'

# ---------- SENTIMENT ANALYSIS FUNCTION ----------
def analyze_sentiment(text):
    """
    Enhanced sentiment analysis for Indian context
    """
    # Remove emojis for TextBlob analysis
    text_clean = ''.join(c for c in text if c not in emoji.EMOJI_DATA)
    
    # Get emoji sentiment
    text_emojis = ''.join(c for c in text if c in emoji.EMOJI_DATA)
    emoji_sentiment = 0
    
    if text_emojis:
        positive_emojis = ["😊", "😁", "😄", "😍", "👍", "✅", "💚", "🎉", "👌", "😀"]
        negative_emojis = ["😠", "😡", "🤬", "💢", "👎", "❌", "💔", "😞", "😢", "😤"]
        
        for emoji_char in text_emojis:
            if emoji_char in positive_emojis:
                emoji_sentiment += 0.3
            elif emoji_char in negative_emojis:
                emoji_sentiment -= 0.3
    
    # TextBlob sentiment
    blob = TextBlob(text_clean)
    polarity = blob.sentiment.polarity + emoji_sentiment
    
    # Clamp polarity between -1 and 1
    polarity = max(-1, min(1, polarity))
    
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    else:
        return "neutral"

# ---------- LOAD TWEETS ----------
input_path = "backend/data.json"
if not os.path.exists(input_path):
    print("❌ 'data.json' not found. Run scraper first.")
    exit()

with open(input_path, "r", encoding="utf-8") as f:
    tweets = json.load(f)

if not tweets:
    print("⚠️ No tweets to process.")
    exit()

# ---------- CONNECT TO MYSQL ----------
try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print("✅ Connected to MySQL.")

    # ---------- VERIFY TABLE STRUCTURE ----------
    cursor.execute("DESCRIBE tweet_sentiment")
    columns = cursor.fetchall()
    print("📋 Current table structure:")
    for col in columns:
        print(f"   {col[0]} - {col[1]}")

    inserted = 0
    for tweet in tweets:
        tweet_id = tweet['id']
        text = tweet['text']
        sentiment = analyze_sentiment(text)
        created_at = tweet['created_at'].replace("Z", "")
        
        # Detect region (state/city)
        region = detect_region_from_text(text)

        try:
            cursor.execute("""
                INSERT INTO tweet_sentiment (id, text, created_at, sentiment, region)
                VALUES (%s, %s, %s, %s, %s)
            """, (tweet_id, text, created_at, sentiment, region))
            inserted += 1
        except mysql.connector.IntegrityError:
            # Skip duplicates
            continue

    conn.commit()
    print(f"💾 Uploaded {inserted} new tweet records to MySQL.")
    
    # Print summary by region
    cursor.execute("""
        SELECT region, COUNT(*) as count, 
               SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive,
               SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative,
               SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral
        FROM tweet_sentiment 
        GROUP BY region 
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    print("\n📊 REGION-WISE SUMMARY:")
    print("=" * 80)
    for row in results:
        region, count, positive, negative, neutral = row
        sentiment_ratio = (positive - negative) / count if count > 0 else 0
        print(f"{region:30} | Messages: {count:4} | Sentiment: {sentiment_ratio:+.2f} | +{positive} -{negative} ={neutral}")

except mysql.connector.Error as e:
    print("❌ MySQL Error:", e)

finally:
    if 'cursor' in locals(): cursor.close()
    if 'conn' in locals(): conn.close()