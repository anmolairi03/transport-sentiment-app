import os
import mysql.connector
from mysql.connector import Error
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Connect to MySQL database"""
        try:
            # Try environment variables first (for Render deployment)
            if os.getenv('MYSQL_HOST'):
                config = {
                    'host': os.getenv('MYSQL_HOST'),
                    'database': os.getenv('MYSQL_DATABASE'),
                    'user': os.getenv('MYSQL_USER'),
                    'password': os.getenv('MYSQL_PASSWORD'),
                    'port': int(os.getenv('MYSQL_PORT', 3306)),
                    'charset': 'utf8mb4',
                    'collation': 'utf8mb4_unicode_ci',
                    'autocommit': True
                }
            else:
                # Fallback for local development
                config = {
                    'host': 'localhost',
                    'database': 'transport_sentiment_app',
                    'user': 'root',
                    'password': 'gadheullu12',
                    'port': 3306,
                    'charset': 'utf8mb4',
                    'collation': 'utf8mb4_unicode_ci',
                    'autocommit': True
                }
            
            self.connection = mysql.connector.connect(**config)
            logger.info("✅ Connected to MySQL database")
            self.create_tables()
            
        except Error as e:
            logger.error(f"❌ MySQL connection failed: {e}")
            self.connection = None
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        if not self.connection:
            return
        
        try:
            cursor = self.connection.cursor()
            
            # Create tweets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tweet_sentiment (
                    id VARCHAR(255) PRIMARY KEY,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sentiment VARCHAR(20) DEFAULT 'neutral',
                    region VARCHAR(255) DEFAULT 'India',
                    source VARCHAR(50) DEFAULT 'unknown',
                    transport_type VARCHAR(20) DEFAULT 'bus',
                    sentiment_score DECIMAL(3,2) DEFAULT 0.0,
                    confidence DECIMAL(3,2) DEFAULT 0.5,
                    INDEX idx_created_at (created_at),
                    INDEX idx_sentiment (sentiment),
                    INDEX idx_region (region),
                    INDEX idx_transport_type (transport_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            # Create states summary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS state_summary (
                    state VARCHAR(255) PRIMARY KEY,
                    total_messages INTEGER DEFAULT 0,
                    positive_count INTEGER DEFAULT 0,
                    negative_count INTEGER DEFAULT 0,
                    neutral_count INTEGER DEFAULT 0,
                    avg_sentiment DECIMAL(3,2) DEFAULT 0.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_total_messages (total_messages),
                    INDEX idx_avg_sentiment (avg_sentiment)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            
            self.connection.commit()
            logger.info("✅ MySQL tables created/verified")
            
        except Error as e:
            logger.error(f"❌ Error creating tables: {e}")
            if self.connection:
                self.connection.rollback()
    
    def insert_tweet(self, tweet_data):
        """Insert a tweet into the database"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT IGNORE INTO tweet_sentiment 
                (id, text, created_at, sentiment, region, source, transport_type, sentiment_score, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                tweet_data['id'],
                tweet_data['text'],
                tweet_data.get('created_at'),
                tweet_data.get('sentiment', 'neutral'),
                tweet_data.get('region', 'India'),
                tweet_data.get('source', 'unknown'),
                tweet_data.get('transport_type', 'bus'),
                tweet_data.get('sentiment_score', 0.0),
                tweet_data.get('confidence', 0.5)
            ))
            
            self.connection.commit()
            return True
            
        except Error as e:
            logger.error(f"❌ Error inserting tweet: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_recent_tweets(self, limit=100):
        """Get recent tweets from database"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM tweet_sentiment 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            
            return cursor.fetchall()
            
        except Error as e:
            logger.error(f"❌ Error fetching tweets: {e}")
            return []
    
    def get_state_summary(self):
        """Get aggregated data by state"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    region,
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(CASE WHEN transport_type = 'bus' THEN 1 END) as bus_count,
                    COUNT(CASE WHEN transport_type = 'metro' THEN 1 END) as metro_count,
                    COUNT(CASE WHEN transport_type = 'train' THEN 1 END) as train_count,
                    COUNT(CASE WHEN transport_type = 'auto' THEN 1 END) as auto_count,
                    COUNT(CASE WHEN transport_type = 'taxi' THEN 1 END) as taxi_count
                FROM tweet_sentiment 
                GROUP BY region
                ORDER BY total_messages DESC
            """)
            
            return cursor.fetchall()
            
        except Error as e:
            logger.error(f"❌ Error fetching state summary: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")

# Global database instance
db = Database()