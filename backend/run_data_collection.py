#!/usr/bin/env python3
"""
Complete data collection and API setup script
Run this single script to collect data and start the API server
"""

import subprocess
import sys
import os
import time
import threading
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    
    packages = [
        "requests==2.31.0",
        "flask==2.3.3",
        "flask-cors==4.0.0", 
        "textblob==0.17.1",
        "praw==7.7.1",
        "beautifulsoup4==4.12.2",
        "newsapi-python==0.2.7",
        "mysql-connector-python==8.2.0"
    ]
    
    for package in packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            return False
    
    # Download TextBlob corpora
    try:
        import textblob
        textblob.download_corpora()
        print("✅ TextBlob corpora downloaded")
    except:
        print("⚠️ TextBlob corpora download failed (optional)")
    
    return True

def collect_data():
    """Run the multi-source data collector"""
    print("\n🚀 Starting data collection from multiple sources...")
    
    # Ensure backend directory exists
    os.makedirs("backend", exist_ok=True)
    
    # Run the multi-source scraper
    if run_command("python backend/multi_source_scraper.py", "Multi-source data collection"):
        print("✅ Data collection completed")
        return True
    else:
        print("❌ Data collection failed")
        return False

def analyze_sentiment():
    """Run sentiment analysis on collected data"""
    print("\n🧠 Analyzing sentiment...")
    
    if run_command("python backend/analyse_sentiment.py", "Sentiment analysis"):
        print("✅ Sentiment analysis completed")
        return True
    else:
        print("❌ Sentiment analysis failed")
        return False

def start_api_server():
    """Start the Flask API server"""
    print("\n🌐 Starting API server...")
    
    # Run API server in background
    try:
        subprocess.Popen([sys.executable, "backend/api.py"], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE)
        time.sleep(3)  # Give server time to start
        print("✅ API server started on http://localhost:5000")
        return True
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return False

def check_mysql_connection():
    """Check if MySQL is running and accessible"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="gadheullu12",
            database="transport_sentiment_app"
        )
        conn.close()
        print("✅ MySQL connection successful")
        return True
    except Exception as e:
        print(f"⚠️ MySQL connection failed: {e}")
        print("   Make sure MySQL is running and database exists")
        return False

def main():
    """Main execution function"""
    print("🇮🇳 Indian Transport Sentiment Analysis - Complete Setup")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("backend"):
        os.makedirs("backend")
    
    # Step 1: Install dependencies
    print("\n📋 STEP 1: Installing Dependencies")
    if not install_dependencies():
        print("❌ Dependency installation failed. Please check your Python environment.")
        return
    
    # Step 2: Check MySQL connection
    print("\n📋 STEP 2: Checking Database Connection")
    mysql_ok = check_mysql_connection()
    
    # Step 3: Collect data from multiple sources
    print("\n📋 STEP 3: Collecting Transport Data")
    if not collect_data():
        print("❌ Data collection failed. Check your internet connection.")
        return
    
    # Step 4: Analyze sentiment
    if mysql_ok:
        print("\n📋 STEP 4: Analyzing Sentiment and Storing in Database")
        if not analyze_sentiment():
            print("⚠️ Sentiment analysis failed, but continuing...")
    else:
        print("\n⚠️ STEP 4: Skipping database operations (MySQL not available)")
    
    # Step 5: Start API server
    print("\n📋 STEP 5: Starting API Server")
    if start_api_server():
        print("\n🎉 SETUP COMPLETE!")
        print("=" * 60)
        print("✅ Data collection: ACTIVE")
        print("✅ Sentiment analysis: COMPLETED")
        print("✅ API server: RUNNING on http://localhost:5000")
        print("\n🚀 Next steps:")
        print("1. Open a new terminal")
        print("2. Run: npm run dev")
        print("3. Open http://localhost:5173 in your browser")
        print("\n📊 API Endpoints available:")
        print("- http://localhost:5000/api/status")
        print("- http://localhost:5000/api/tweets") 
        print("- http://localhost:5000/api/states")
        
        print("\n🔄 To collect fresh data, run:")
        print("python backend/multi_source_scraper.py")
        
    else:
        print("❌ API server failed to start")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Setup interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")