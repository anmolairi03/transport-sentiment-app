// API service for real-time data fetching
const API_BASE_URL = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api`
  : 'http://localhost:5000/api';

export interface RealTimeTweet {
  id: string;
  text: string;
  timestamp: string;
  location: string;
  state: string;
  transportType: 'bus' | 'metro' | 'train' | 'auto' | 'taxi';
  sentiment: {
    polarity: number;
    label: 'positive' | 'negative' | 'neutral';
    confidence: number;
  };
}

export interface RealTimeStateData {
  state: string;
  sentimentScore: number;
  totalMessages: number;
  transportBreakdown: {
    bus: number;
    metro: number;
    train: number;
    auto: number;
    taxi: number;
  };
  sentimentBreakdown: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

class ApiService {
  private static instance: ApiService;
  private isConnected: boolean = false;

  static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService();
    }
    return ApiService.instance;
  }

  async checkConnection(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/status`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });
      this.isConnected = response.ok;
      return this.isConnected;
    } catch (error) {
      console.warn('API connection failed - using mock data:', error instanceof Error ? error.message : 'Unknown error');
      this.isConnected = false;
      return false;
    }
  }

  async fetchRealTimeTweets(): Promise<RealTimeTweet[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/tweets`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const tweets = await response.json();
      return tweets.map(this.transformTweet);
    } catch (error) {
      console.error('Failed to fetch tweets:', error);
      return [];
    }
  }

  async fetchRealTimeStates(): Promise<RealTimeStateData[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/states`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch states:', error);
      return [];
    }
  }

  private transformTweet(apiTweet: any): RealTimeTweet {
    return {
      id: apiTweet.id,
      text: apiTweet.text,
      timestamp: apiTweet.timestamp,
      location: `${apiTweet.location}, ${apiTweet.state}`,
      state: apiTweet.state,
      transportType: apiTweet.transportType,
      sentiment: {
        polarity: apiTweet.sentiment.polarity,
        label: apiTweet.sentiment.label,
        confidence: apiTweet.sentiment.confidence
      }
    };
  }

  isApiConnected(): boolean {
    return this.isConnected;
  }
}

export const apiService = ApiService.getInstance();