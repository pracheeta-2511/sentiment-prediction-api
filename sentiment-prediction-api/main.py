import re
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from textblob import TextBlob

app = FastAPI()
templates = Jinja2Templates(directory="templates")

API_KEY = "YOUR_YOUTUBE_API"
youtube = build('youtube', 'v3', developerKey=API_KEY)

def clean_text(text):
    text = re.sub(r"(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", text)
    return ' '.join(text.split())

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return "<h1>Dashboard is ready. Go to /analyze/[VIDEO_ID]</h1>"

@app.get("/analyze/{video_id}", response_class=HTMLResponse)
def analyze_comments(request: Request, video_id: str):
    try:
        # Fetch 20 comments from the video
        yt_request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=20,
            textFormat="plainText"
        )
        response = yt_request.execute()

        results = []
        stats = {"Positive": 0, "Negative": 0, "Neutral": 0}
        
        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            cleaned = clean_text(comment)
            polarity = TextBlob(cleaned).sentiment.polarity
            
            sentiment = "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"
            stats[sentiment] += 1
            results.append({"text": comment, "sentiment": sentiment})

        return templates.TemplateResponse("index.html", {
            "request": request,
            "video_id": video_id,
            "analysis": results,
            "stats": stats
        })

    except HttpError as e:
        return HTMLResponse(content=f"<h1>YouTube API Error</h1><p>{str(e)}</p>", status_code=400)
    except Exception as e:
        return HTMLResponse(content=f"<h1>System Error</h1><p>{str(e)}</p>", status_code=500)

# Additional Sidebar Routes
@app.get("/history", response_class=HTMLResponse)
def get_history(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/api-docs", response_class=HTMLResponse)
def get_api_docs(request: Request):
    return templates.TemplateResponse("docs_info.html", {"request": request})

@app.get("/settings", response_class=HTMLResponse)
def get_settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})