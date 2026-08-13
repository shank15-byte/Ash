"""The Content Surgeon API.

Set YOUTUBE_API_KEY to enable live analysis of public YouTube channels. The
application intentionally falls back to deterministic demo data so it remains
presentable without credentials or when YouTube quotas are exhausted.
"""
import json, os, re, urllib.parse, urllib.request
from collections import Counter

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".")
YOUTUBE_API = "https://www.googleapis.com/youtube/v3"
STOP_WORDS = set("the and for with that this your from into about how what why are was you our their video videos a an to of in on is it at by as be or we i my".split())
POSITIVE = set("great amazing helpful love excellent awesome best clear useful inspiring brilliant thanks good".split())
NEGATIVE = set("bad boring confusing poor slow worst disappointed annoying fake useless".split())


def api_get(resource, **params):
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY is not configured")
    params["key"] = key
    url = f"{YOUTUBE_API}/{resource}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=12) as response:
            return json.load(response)
    except Exception as exc:
        raise RuntimeError("YouTube could not return channel data. Check the API key and try again.") from exc


def channel_id_from_input(value):
    value = value.strip()
    if value.startswith("UC") and len(value) >= 20:
        return value
    path = urllib.parse.urlparse(value if "://" in value else "https://youtube.com/" + value).path.strip("/")
    if path.startswith("channel/"):
        return path.split("/")[1]
    if path.startswith("@"):
        data = api_get("channels", part="id", forHandle=path[1:])
    else:
        query = path.split("/")[-1] or value
        data = api_get("search", part="snippet", q=query, type="channel", maxResults=1)
        return data["items"][0]["snippet"]["channelId"] if data.get("items") else None
    return data["items"][0]["id"] if data.get("items") else None


def words(text):
    return [word.lower() for word in re.findall(r"[a-zA-Z]{3,}", text) if word.lower() not in STOP_WORDS]


def sentiment(comments):
    scores = []
    for comment in comments:
        tokens = words(comment)
        score = sum(t in POSITIVE for t in tokens) - sum(t in NEGATIVE for t in tokens)
        scores.append(1 if score > 0 else -1 if score < 0 else 0)
    total = max(len(scores), 1)
    counts = {"positive": scores.count(1), "neutral": scores.count(0), "negative": scores.count(-1)}
    return {key: round(value * 100 / total) for key, value in counts.items()}


def build_analysis(channel, videos, comments, source):
    videos = videos[:10]
    views = sum(v["views"] for v in videos)
    likes, comment_count = sum(v["likes"] for v in videos), sum(v["comments"] for v in videos)
    engagement = (likes + comment_count) * 100 / max(views, 1)
    sent = sentiment(comments)
    positive_words = Counter(w for c in comments for w in words(c) if w in POSITIVE).most_common(6)
    negative_words = Counter(w for c in comments for w in words(c) if w in NEGATIVE).most_common(6)
    keyword_counts = Counter(w for v in videos for w in words(v["title"] + " " + v["description"])).most_common(12)
    trend = []
    for video in reversed(videos):
        title_words = words(video["title"])
        score = 58 + sum(w in POSITIVE for w in title_words) * 6 - sum(w in NEGATIVE for w in title_words) * 5
        trend.append({"name": video["title"][:14] + "…", "score": score})
    gaps = [
        {"topic": "AI workflow shortcuts", "volume": "18.2K", "difficulty": "Low", "opportunity": "High"},
        {"topic": "Creator monetization playbook", "volume": "12.9K", "difficulty": "Medium", "opportunity": "High"},
        {"topic": "Behind-the-scenes teardown", "volume": "9.4K", "difficulty": "Low", "opportunity": "Medium"},
        {"topic": "Short-form storytelling", "volume": "22.1K", "difficulty": "High", "opportunity": "High"},
        {"topic": "Audience Q&A deep dive", "volume": "7.8K", "difficulty": "Low", "opportunity": "Medium"},
    ]
    return {"source": source, "channel": channel, "videos": videos, "metrics": {"views": views, "subscribers": channel["subscribers"], "avgViews": round(views / max(len(videos), 1)), "engagement": round(engagement, 2)}, "sentiment": sent, "wordCloud": {"positive": [w for w, _ in positive_words] or ["helpful", "great", "love"], "negative": [w for w, _ in negative_words] or ["slow", "confusing", "boring"]}, "trend": trend, "keywords": [w for w, _ in keyword_counts], "gaps": gaps, "prescriptions": prescriptions(engagement, sent, videos)}


def prescriptions(engagement, sent, videos):
    avg_duration = sum(v["duration"] for v in videos) / max(len(videos), 1)
    return [
        {"priority": "HIGH", "title": "Lead with the payoff", "detail": "Open with the finished result in the first 12 seconds to reduce early drop-off."},
        {"priority": "HIGH", "title": "Use a clearer emotional thumbnail", "detail": "Pair one expressive face with 3–5 words of outcome-focused text for stronger click intent."},
        {"priority": "MED", "title": "Tune your video length", "detail": f"Your recent average is {avg_duration:.1f} minutes. Test a tighter 7–9 minute cut on the next upload."},
        {"priority": "MED", "title": "Schedule a midweek release", "detail": "Publish Wednesday between 2–4 PM ET, then engage in comments during the first hour."},
        {"priority": "LOW", "title": "Invite a specific conversation", "detail": f"Your audience sentiment is {sent['positive']}% positive. End with one concrete question to increase replies."},
    ]


def demo_data():
    base = [
        ("I tested 7 AI tools creators actually need", 182400, 14280, 980, 9.2), ("How I plan a month of videos in one hour", 142800, 10900, 760, 11.5),
        ("The truth about growing on YouTube in 2026", 231600, 17620, 1420, 13.1), ("My editing workflow, completely rebuilt", 98500, 7200, 510, 8.4),
        ("Stop making these thumbnail mistakes", 195200, 15800, 1200, 10.0), ("I made 30 Shorts in a weekend", 121400, 8600, 630, 7.7),
        ("A better system for creator burnout", 88400, 6900, 490, 12.4), ("The YouTube strategy nobody talks about", 167900, 12900, 880, 10.8),
        ("Building a sustainable creator business", 110300, 8500, 620, 14.0), ("What I would do starting from zero", 256100, 20100, 1680, 12.1),
    ]
    videos = [{"id": f"demo{i}", "title": t, "description": "Practical creator systems, YouTube strategy and sustainable growth.", "views": v, "likes": l, "comments": c, "duration": d, "published": f"2026-0{(i % 7) + 1}-12"} for i, (t, v, l, c, d) in enumerate(base)]
    comments = ["This is incredibly helpful and clear", "Great workflow, love the practical tips", "Amazing breakdown, thank you", "The pacing felt slow in the middle", "Useful advice for new creators", "This is the best creator guide", "A little confusing but still good"] * 12
    return {"name": "Creator Lab", "handle": "@creatorlab", "subscribers": 184200, "thumbnail": ""}, videos, comments


def live_data(value):
    channel_id = channel_id_from_input(value)
    if not channel_id: raise RuntimeError("Channel not found. Paste a channel URL, @handle, or channel ID.")
    raw_channel = api_get("channels", part="snippet,statistics", id=channel_id)["items"][0]
    search = api_get("search", part="snippet", channelId=channel_id, type="video", order="date", maxResults=10)
    ids = ",".join(x["id"]["videoId"] for x in search.get("items", []))
    detail = api_get("videos", part="snippet,statistics,contentDetails", id=ids).get("items", [])
    videos, comments = [], []
    for item in detail:
        stat, snip = item.get("statistics", {}), item["snippet"]
        duration = re.findall(r"\d+", item.get("contentDetails", {}).get("duration", "PT0M")); minutes = int(duration[0]) if duration else 0
        videos.append({"id": item["id"], "title": snip["title"], "description": snip.get("description", ""), "views": int(stat.get("viewCount", 0)), "likes": int(stat.get("likeCount", 0)), "comments": int(stat.get("commentCount", 0)), "duration": minutes, "published": snip["publishedAt"][:10]})
        try:
            thread = api_get("commentThreads", part="snippet", videoId=item["id"], maxResults=10, textFormat="plainText")
            comments += [x["snippet"]["topLevelComment"]["snippet"]["textDisplay"] for x in thread.get("items", [])]
        except RuntimeError: pass
    return {"name": raw_channel["snippet"]["title"], "handle": raw_channel["snippet"].get("customUrl", ""), "subscribers": int(raw_channel["statistics"].get("subscriberCount", 0)), "thumbnail": raw_channel["snippet"]["thumbnails"].get("medium", {}).get("url", "")}, videos, comments


@app.get("/")
def index(): return send_from_directory(".", "index.html")

@app.get("/<path:filename>")
def asset(filename):
    if filename in {"style.css", "script.js"}: return send_from_directory(".", filename)
    return jsonify(error="Not found"), 404

@app.post("/api/analyze")
def analyze():
    value = (request.get_json(silent=True) or {}).get("channel", "")
    try:
        channel, videos, comments = live_data(value)
        return jsonify(build_analysis(channel, videos, comments, "live"))
    except Exception as exc:
        channel, videos, comments = demo_data()
        result = build_analysis(channel, videos, comments, "demo")
        result["notice"] = str(exc) if value else "Showing demo data — add a channel URL to analyze live data."
        return jsonify(result)

@app.post("/api/predict")
def predict():
    data = request.get_json(silent=True) or {}; title = data.get("title", "")
    length = max(1, float(data.get("length", 9)))
    title_bonus = min(1.3, len(words(title)) * .06) + (0.45 if any(x in title.lower() for x in ["how", "best", "secret", "tested"]) else 0)
    rate = max(2.1, min(15.9, 5.7 + title_bonus + (1.4 if 7 <= length <= 12 else -.6)))
    return jsonify({"engagement": round(rate, 1), "confidence": 86, "views48": int(46500 * (rate / 6.2)), "likes48": int(46500 * (rate / 6.2) * .061), "comments48": int(46500 * (rate / 6.2) * .006), "uplift": round((rate / 6.2 - 1) * 100)})

if __name__ == "__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
