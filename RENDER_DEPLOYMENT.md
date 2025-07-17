# 🚀 Deploy Transport Sentiment App on Render

## Step-by-Step Deployment Guide

### 1. **Prepare Your Code**

First, make sure all files are ready:
```bash
# Check that you have these key files:
ls render.yaml                    # ✅ Deployment configuration
ls backend/requirements.txt       # ✅ Python dependencies
ls backend/database.py            # ✅ PostgreSQL database handler
ls backend/api.py                 # ✅ Flask API server
ls backend/multi_source_scraper.py # ✅ Data collector
```

### 2. **Push to GitHub**

```bash
# Initialize git repository
git init

# Add all files
git add .

# Commit changes
git commit -m "Transport sentiment app ready for Render deployment"

# Create GitHub repository and push
git remote add origin https://github.com/YOUR_USERNAME/transport-sentiment-app.git
git branch -M main
git push -u origin main
```

### 3. **Deploy on Render**

1. **Go to Render Dashboard:**
   - Visit [render.com](https://render.com)
   - Sign up or log in with GitHub

2. **Create New Blueprint:**
   - Click **"New"** → **"Blueprint"**
   - Connect your GitHub account
   - Select your `transport-sentiment-app` repository

3. **Automatic Deployment:**
   - Render will detect the `render.yaml` file
   - It will automatically create:
     - ✅ PostgreSQL Database
     - ✅ Backend API Service
     - ✅ Frontend Web Service
     - ✅ Background Data Collector (Cron Job)

4. **Wait for Build:**
   - Backend: ~3-5 minutes
   - Frontend: ~2-3 minutes
   - Database: ~1 minute

### 4. **Your Deployed URLs**

After deployment, you'll get:
- **Frontend**: `https://transport-sentiment-frontend.onrender.com`
- **API**: `https://transport-sentiment-api.onrender.com`
- **Health Check**: `https://transport-sentiment-api.onrender.com/api/health`

### 5. **Verify Deployment**

Test these endpoints:
```bash
# Health check
curl https://transport-sentiment-api.onrender.com/api/health

# API status
curl https://transport-sentiment-api.onrender.com/api/status

# Get tweets
curl https://transport-sentiment-api.onrender.com/api/tweets

# Get states data
curl https://transport-sentiment-api.onrender.com/api/states
```

## 🔧 **What Happens During Deployment**

### **Backend Service:**
1. Installs Python dependencies
2. Downloads TextBlob language models
3. Connects to PostgreSQL database
4. Creates necessary tables
5. Starts Flask API server on port 5000

### **Frontend Service:**
1. Installs Node.js dependencies
2. Builds React app with Vite
3. Serves static files
4. Connects to backend API

### **Database:**
1. Creates PostgreSQL instance
2. Sets up `tweet_sentiment` table
3. Configures connection string

### **Background Job:**
1. Runs data collection every 2 hours
2. Collects from Reddit, News APIs, web scraping
3. Analyzes sentiment and stores in database

## 🎯 **Environment Variables (Pre-configured)**

All API keys are already set in `render.yaml`:
- ✅ **Reddit API**: `u2cLai036-BFLeZTrlVrDQ`
- ✅ **News API**: `5189820e12d74b9fa076fc032be614d5`
- ✅ **Database**: Auto-configured by Render
- ✅ **CORS**: Configured for cross-origin requests

## 🔍 **Monitoring Your App**

### **Check Logs:**
1. Go to Render Dashboard
2. Click on your service
3. View **"Logs"** tab for real-time output

### **Monitor Data Collection:**
- Check `/api/status` for database stats
- View `/api/tweets` for recent data
- Monitor cron job logs for collection status

## 🚨 **Troubleshooting**

### **Build Failures:**
```bash
# If Python build fails:
- Check backend/requirements.txt syntax
- Ensure all dependencies are compatible

# If Node build fails:
- Check package.json dependencies
- Verify Vite configuration
```

### **Database Connection Issues:**
```bash
# Check database logs in Render dashboard
# Verify DATABASE_URL environment variable
# Ensure PostgreSQL service is running
```

### **API Not Responding:**
```bash
# Check backend service logs
# Verify PORT environment variable (should be 5000)
# Test health endpoint: /api/health
```

## 💰 **Cost Optimization**

### **Free Tier Limits:**
- ✅ **Web Services**: 750 hours/month (enough for 1 service)
- ✅ **Cron Jobs**: 400 hours/month
- ✅ **PostgreSQL**: 1GB storage, 1 million rows
- ✅ **Bandwidth**: 100GB/month

### **Optimization Tips:**
1. **Efficient Data Collection**: Runs every 2 hours (not continuously)
2. **Database Cleanup**: Automatically removes old data
3. **Caching**: Frontend caches API responses
4. **Compression**: Gzip enabled for all responses

## 🎉 **Success Indicators**

Your deployment is successful when:
- ✅ Frontend loads the India map visualization
- ✅ Backend API returns transport sentiment data
- ✅ Database stores and retrieves data correctly
- ✅ Background job collects data every 2 hours
- ✅ Real-time updates appear on the map

## 📞 **Support**

If you encounter issues:
1. Check Render service logs
2. Verify all environment variables
3. Test API endpoints individually
4. Check database connection status

Your transport sentiment monitoring system will be live and collecting data from across India! 🇮🇳