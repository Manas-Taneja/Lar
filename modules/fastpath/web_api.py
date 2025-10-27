# modules/fastpath/web_api.py
import requests
import feedparser

# --- Weather Query ---
def handle_weather_query(text: str) -> str:
    """Gets the current weather from wttr.in."""
    try:
        response = requests.get("https://wttr.in/?format=%C+%t")
        response.raise_for_status() # Raise error for bad responses
        weather_data = response.text.strip()
        return f"The current weather is {weather_data}."
    except requests.RequestException as e:
        print(f"Weather API error: {e}")
        return "Sorry, I couldn't get the weather right now."

# --- News Query ---
NEWS_FEED_URL = "http://feeds.bbci.co.uk/news/world/rss.xml"

def handle_news_query(text: str) -> str:
    """Gets the top news headline from an RSS feed."""
    try:
        feed = feedparser.parse(NEWS_FEED_URL)
        if not feed.entries:
            return "Sorry, I couldn't retrieve any headlines."
        
        top_headline = feed.entries[0].title
        return f"The latest headline is: {top_headline}"
    except Exception as e:
        print(f"News feed error: {e}")
        return "Sorry, I couldn't get the news right now."