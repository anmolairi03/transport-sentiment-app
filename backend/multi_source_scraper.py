#!/usr/bin/env python3
"""
Multi-source transport data collector
Replaces Twitter API with multiple free, faster sources
"""

import requests
import json
import time
from datetime import datetime, timezone
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import praw
from textblob import TextBlob
import os

# Configuration
REDDIT_CLIENT_ID = "u2cLai036-BFLeZTrlVrDQ"
REDDIT_CLIENT_SECRET = "g1BpKHMPRt_M6jYBOxm_-HzGwbKpDw"
NEWS_API_KEY = "5189820e12d74b9fa076fc032be614d5"  # Free from newsapi.org

# Indian transport-related subreddits
TRANSPORT_SUBREDDITS = [
    'india', 'mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata',
    'hyderabad', 'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kochi',
    'IndianRailways', 'DelhiMetro', 'MumbaiTrains'
]

# News sources for transport
NEWS_SOURCES = [
    'the-times-of-india',
    'the-hindu',
    'indian-express',
    'hindustan-times'
]

# Transport keywords for filtering
TRANSPORT_KEYWORDS = [
    'bus', 'metro', 'train', 'railway', 'transport', 'traffic',
    'auto rickshaw', 'taxi', 'uber', 'ola', 'bmtc', 'best',
    'dtc', 'dmrc', 'irctc', 'local train', 'city bus'
]

class MultiSourceCollector:
    def __init__(self):
        self.reddit = None
        self.session = requests.Session()
        self.collected_data = []
        
    def setup_reddit(self):
        """Initialize Reddit API client"""
        try:
            self.reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent="IndianTransportMonitor/1.0"
            )
            print("✅ Reddit API initialized")
            return True
        except Exception as e:
            print(f"❌ Reddit setup failed: {e}")
            return False
    
    def collect_reddit_data(self, limit=50):
        """Collect transport discussions from Reddit"""
        if not self.reddit:
            return []
        
        reddit_data = []
        
        for subreddit_name in TRANSPORT_SUBREDDITS:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search for transport-related posts
                for submission in subreddit.search(
                    "transport OR bus OR metro OR train OR traffic", 
                    limit=limit//len(TRANSPORT_SUBREDDITS),
                    time_filter='day'
                ):
                    # Process submission
                    data = {
                        'id': f"reddit_{submission.id}",
                        'text': f"{submission.title} {submission.selftext}",
                        'created_at': datetime.fromtimestamp(submission.created_utc, timezone.utc).isoformat(),
                        'source': 'reddit',
                        'location': self.detect_location(submission.title + " " + submission.selftext),
                        'url': f"https://reddit.com{submission.permalink}",
                        'score': submission.score,
                        'subreddit': subreddit_name
                    }
                    reddit_data.append(data)
                    
                    # Also collect top comments
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments[:3]:  # Top 3 comments
                        if len(comment.body) > 20:  # Filter short comments
                            comment_data = {
                                'id': f"reddit_comment_{comment.id}",
                                'text': comment.body,
                                'created_at': datetime.fromtimestamp(comment.created_utc, timezone.utc).isoformat(),
                                'source': 'reddit_comment',
                                'location': self.detect_location(comment.body),
                                'url': f"https://reddit.com{submission.permalink}",
                                'score': comment.score,
                                'subreddit': subreddit_name
                            }
                            reddit_data.append(comment_data)
                
                time.sleep(1)  # Be respectful to Reddit API
                
            except Exception as e:
                print(f"❌ Error collecting from r/{subreddit_name}: {e}")
                continue
        
        print(f"✅ Collected {len(reddit_data)} items from Reddit")
        return reddit_data
    
    def collect_news_data(self):
        """Collect transport news from News API"""
        if not NEWS_API_KEY or NEWS_API_KEY == "your_news_api_key":
            return []
        
        news_data = []
        
        try:
            # Search for transport-related news
            url = "https://newsapi.org/v2/everything"
            params = {
                'apiKey': NEWS_API_KEY,
                'q': 'india transport OR mumbai metro OR delhi bus OR bangalore traffic',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 50,
                'from': datetime.now().strftime('%Y-%m-%d')
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                
                for article in articles:
                    data = {
                        'id': f"news_{hash(article['url'])}",
                        'text': f"{article['title']} {article.get('description', '')}",
                        'created_at': article['publishedAt'],
                        'source': 'news',
                        'location': self.detect_location(article['title'] + " " + article.get('description', '')),
                        'url': article['url'],
                        'author': article.get('author', 'Unknown'),
                        'source_name': article['source']['name']
                    }
                    news_data.append(data)
            
            print(f"✅ Collected {len(news_data)} news articles")
            
        except Exception as e:
            print(f"❌ Error collecting news data: {e}")
        
        return news_data
    
    def scrape_transport_websites(self):
        """Scrape transport-related websites"""
        scraped_data = []
        
        # Transport websites to scrape
        websites = [
            {
                'url': 'https://www.hindustantimes.com/topic/mumbai-traffic',
                'location': 'Mumbai, Maharashtra'
            },
            {
                'url': 'https://timesofindia.indiatimes.com/topic/delhi-metro',
                'location': 'Delhi'
            }
        ]
        
        for site in websites:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = self.session.get(site['url'], headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract headlines and snippets
                    headlines = soup.find_all(['h1', 'h2', 'h3'], limit=10)
                    
                    for headline in headlines:
                        text = headline.get_text().strip()
                        if any(keyword in text.lower() for keyword in TRANSPORT_KEYWORDS):
                            data = {
                                'id': f"web_{hash(text)}",
                                'text': text,
                                'created_at': datetime.now(timezone.utc).isoformat(),
                                'source': 'web_scraping',
                                'location': site['location'],
                                'url': site['url']
                            }
                            scraped_data.append(data)
                
                time.sleep(2)  # Be respectful
                
            except Exception as e:
                print(f"❌ Error scraping {site['url']}: {e}")
                continue
        
        print(f"✅ Scraped {len(scraped_data)} items from websites")
        return scraped_data
    
    def detect_location(self, text):
        """Detect Indian city/state from text"""
        cities = {
            'mumbai': 'Mumbai, Maharashtra',
            'delhi': 'Delhi',
            'bangalore': 'Bangalore, Karnataka',
            'bengaluru': 'Bangalore, Karnataka',
            'chennai': 'Chennai, Tamil Nadu',
            'kolkata': 'Kolkata, West Bengal',
            'hyderabad': 'Hyderabad, Telangana',
            'pune': 'Pune, Maharashtra',
            'ahmedabad': 'Ahmedabad, Gujarat',
            'jaipur': 'Jaipur, Rajasthan',
            'lucknow': 'Lucknow, Uttar Pradesh',
            'kochi': 'Kochi, Kerala',
            'gurgaon': 'Gurgaon, Haryana',
            'noida': 'Noida, Delhi',
            'chandigarh': 'Chandigarh, Punjab'
        }
        
        text_lower = text.lower()
        for city, location in cities.items():
            if city in text_lower:
                return location
        
        return 'India'  # Default
    
    def analyze_sentiment(self, text):
        """Analyze sentiment using TextBlob"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                label = 'positive'
            elif polarity < -0.1:
                label = 'negative'
            else:
                label = 'neutral'
            
            return {
                'polarity': polarity,
                'label': label,
                'confidence': min(abs(polarity) + 0.5, 1.0)
            }
        except:
            return {
                'polarity': 0,
                'label': 'neutral',
                'confidence': 0.5
            }
    
    def detect_transport_type(self, text):
        """Detect transport type from text"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['metro', 'subway', 'dmrc']):
            return 'metro'
        elif any(word in text_lower for word in ['train', 'railway', 'irctc', 'local']):
            return 'train'
        elif any(word in text_lower for word in ['auto', 'rickshaw', 'three wheeler']):
            return 'auto'
        elif any(word in text_lower for word in ['taxi', 'cab', 'ola', 'uber']):
            return 'taxi'
        else:
            return 'bus'
    
    def collect_all_data(self):
        """Collect data from all sources"""
        print("🚀 Starting multi-source data collection...")
        
        all_data = []
        
        # Collect from Reddit
        if self.setup_reddit():
            reddit_data = self.collect_reddit_data()
            all_data.extend(reddit_data)
        
        # Collect from News API
        news_data = self.collect_news_data()
        all_data.extend(news_data)
        
        # Scrape websites
        scraped_data = self.scrape_transport_websites()
        all_data.extend(scraped_data)
        
        # Process all collected data
        processed_data = []
        for item in all_data:
            # Add sentiment analysis
            item['sentiment'] = self.analyze_sentiment(item['text'])
            
            # Add transport type detection
            item['transport_type'] = self.detect_transport_type(item['text'])
            
            # Extract state from location
            location = item.get('location', 'India')
            if ',' in location:
                item['state'] = location.split(',')[-1].strip()
            else:
                item['state'] = location
            
            processed_data.append(item)
        
        # Remove duplicates based on text similarity
        unique_data = self.remove_duplicates(processed_data)
        
        # Save to file
        os.makedirs("backend", exist_ok=True)
        with open("backend/data.json", "w", encoding="utf-8") as f:
            json.dump(unique_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(unique_data)} unique items to backend/data.json")
        print(f"📊 Sources: Reddit({len([d for d in unique_data if 'reddit' in d['source']])}) | "
              f"News({len([d for d in unique_data if d['source'] == 'news'])}) | "
              f"Web({len([d for d in unique_data if d['source'] == 'web_scraping'])})")
        
        return unique_data
    
    def remove_duplicates(self, data):
        """Remove duplicate entries based on text similarity"""
        unique_data = []
        seen_texts = set()
        
        for item in data:
            # Create a normalized version for comparison
            normalized_text = item['text'].lower().strip()[:100]  # First 100 chars
            
            if normalized_text not in seen_texts:
                seen_texts.add(normalized_text)
                unique_data.append(item)
        
        return unique_data

def main():
    """Main execution function"""
    collector = MultiSourceCollector()
    
    try:
        # Collect data from all sources
        data = collector.collect_all_data()
        
        print("\n📈 COLLECTION SUMMARY:")
        print("=" * 50)
        print(f"Total items collected: {len(data)}")
        
        # Show breakdown by source
        sources = {}
        for item in data:
            source = item['source']
            sources[source] = sources.get(source, 0) + 1
        
        for source, count in sources.items():
            print(f"{source.title()}: {count} items")
        
        # Show sentiment breakdown
        sentiments = {}
        for item in data:
            label = item['sentiment']['label']
            sentiments[label] = sentiments.get(label, 0) + 1
        
        print(f"\nSentiment breakdown:")
        for sentiment, count in sentiments.items():
            print(f"{sentiment.title()}: {count} items")
        
        print(f"\n🚀 Next steps:")
        print("1. Run: python backend/analyse_sentiment.py")
        print("2. Run: python backend/api.py")
        print("3. Start the React frontend")
        
    except KeyboardInterrupt:
        print("\n⏹️ Collection stopped by user")
    except Exception as e:
        print(f"❌ Error during collection: {e}")

if __name__ == "__main__":
    main()