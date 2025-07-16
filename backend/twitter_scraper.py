import requests
import time
import json
from datetime import datetime, timedelta, timezone
import os

# --- CONFIGURATION ---

# Replace with your actual Bearer Token.
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAKti3AEAAAAAJ4n3C9CZbZ6hdfoT9V%2BTuLmfgz8%3DXRCIjqFDeSqKss65Q7zzlYjG4uotxMTbQkhLVeezgNOi7plIbd" 

# Enhanced transport-related queries for all Indian states
QUERIES = [
    # General transport
    "bus india transport",
    "metro india transport", 
    "train india transport",
    "auto rickshaw india",
    "taxi cab india",
    
    # Major cities
    "mumbai local train",
    "delhi metro transport",
    "bangalore traffic bus",
    "chennai bus transport",
    "kolkata metro transport",
    "hyderabad metro bus",
    "pune transport bus",
    "ahmedabad brts bus",
    "jaipur transport bus",
    "lucknow metro transport",
    
    # State transport corporations
    "MSRTC maharashtra bus",
    "DTC delhi bus",
    "BMTC bangalore bus",
    "MTC chennai bus",
    "WBTC kolkata bus",
    "TSRTC telangana bus",
    "PMPML pune bus",
    "GSRTC gujarat bus",
    "RSRTC rajasthan bus",
    "UPSRTC uttar pradesh bus",
    
    # Regional transport
    "north india transport",
    "south india transport", 
    "east india transport",
    "west india transport",
    "central india transport"
]

TWEETS_PER_QUERY = 30  # Reduced to avoid rate limits

# --- SCRIPT START ---

if not BEARER_TOKEN or BEARER_TOKEN == "...":
    print("❌ CRITICAL ERROR: Please replace the '...' in the BEARER_TOKEN variable with your actual Twitter API Bearer Token.")
    exit()

# Headers for Twitter API authentication
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

# --- TIME CALCULATION FUNCTION ---
def get_valid_time_window():
    """
    Calculates a safe start and end time for the Twitter API's 7-day recent search.
    Returns formatted start and end time strings.
    """
    now = datetime.now(timezone.utc)
    end_time = now - timedelta(seconds=30)
    start_time = end_time - timedelta(days=6, hours=23, minutes=50)
    
    start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return start_time_str, end_time_str

# Get the initial time window
start_time_str, end_time_str = get_valid_time_window()

print(f"\n🔍 Fetching tweets from {start_time_str} to {end_time_str}")
print(f"🇮🇳 Searching for transport-related content across Indian states\n")

all_tweets = []
query_count = 0
total_queries = len(QUERIES)

# --- MAIN LOOP ---
for query in QUERIES:
    query_count += 1
    full_query = f"{query} lang:en -is:retweet"
    
    # Use the latest time window for the parameters
    params = {
        "query": full_query,
        "max_results": TWEETS_PER_QUERY,
        "start_time": start_time_str,
        "end_time": end_time_str,
        "tweet.fields": "created_at,lang,author_id,text,public_metrics"
    }

    print(f"🚦 Query {query_count}/{total_queries}: {query}")

    url = "https://api.twitter.com/2/tweets/search/recent"

    try:
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code == 401:
            print("❌ Error: 401 Unauthorized. Your Bearer Token is invalid or expired.")
            print("   Please check your token and try again. Halting script.")
            break 

        # Rate limit handler
        if response.status_code == 429:
            resume_time = datetime.now() + timedelta(minutes=15)
            print(f"⏳ Rate limit hit. Sleeping for 15 minutes.")
            print(f"   Will resume at approximately {resume_time.strftime('%I:%M:%S %p')}.")
            time.sleep(15 * 60)
            
            print("   Resuming request... Recalculating time window.")
            new_start_time, new_end_time = get_valid_time_window()
            params['start_time'] = new_start_time
            params['end_time'] = new_end_time
            print(f"   New Window: {new_start_time} to {new_end_time}")

            response = requests.get(url, headers=HEADERS, params=params)

        # Check the status of the final response
        if response.status_code == 200:
            data = response.json()
            tweets = data.get("data", [])
            print(f"✅ Retrieved {len(tweets)} tweets for '{query}'")
            all_tweets.extend(tweets)
        else:
            print(f"❌ Error: {response.status_code} {response.reason}")
            print(f"Response Body: {response.text}")

        # Add delay between requests to be respectful to the API
        time.sleep(2)

    except requests.exceptions.RequestException as e:
        print(f"❌ A request exception occurred: {e}")

    # Progress indicator
    progress = (query_count / total_queries) * 100
    print(f"📊 Progress: {progress:.1f}% ({query_count}/{total_queries})\n")

# --- SAVE RESULTS ---
if all_tweets:
    os.makedirs("backend", exist_ok=True)
    
    # Remove duplicates based on tweet ID
    unique_tweets = {}
    for tweet in all_tweets:
        unique_tweets[tweet['id']] = tweet
    
    unique_tweets_list = list(unique_tweets.values())
    
    with open("backend/data.json", "w", encoding="utf-8") as f:
        json.dump(unique_tweets_list, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved {len(unique_tweets_list)} unique tweets to 'backend/data.json'")
    print(f"📊 Total queries processed: {query_count}")
    print(f"🔄 Duplicates removed: {len(all_tweets) - len(unique_tweets_list)}")
    
    # Print summary statistics
    print("\n📈 COLLECTION SUMMARY:")
    print("=" * 50)
    print(f"Total unique tweets: {len(unique_tweets_list)}")
    print(f"Queries executed: {query_count}/{total_queries}")
    print(f"Average tweets per query: {len(unique_tweets_list)/query_count:.1f}")
    
    print("\n🚀 Next steps:")
    print("1. Run: python backend/analyse_sentiment.py")
    print("2. Run: python backend/api.py")
    print("3. Start the React frontend")
    
else:
    print("\n⚠️ No tweets were found or saved.")
    print("This could be due to:")
    print("- Rate limiting")
    print("- No matching tweets in the time window")
    print("- API connectivity issues")