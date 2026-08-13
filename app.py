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


def comment_label(comment):
    tokens = words(comment)
    score = sum(t in POSITIVE for t in tokens) - sum(t in NEGATIVE for t in tokens)
    return "positive" if score > 0 else "negative" if score < 0 else "neutral"


def sentiment(comments):
    scores = [comment_label(comment) for comment in comments]
    total = max(len(scores), 1)
    counts = {"positive": scores.count("positive"), "neutral": scores.count("neutral"), "negative": scores.count("negative")}
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
    return {"source": source, "channel": channel, "videos": videos, "metrics": {"views": views, "subscribers": channel["subscribers"], "avgViews": round(views / max(len(videos), 1)), "engagement": round(engagement, 2)}, "sentiment": sent, "comments": [{"text": comment, "sentiment": comment_label(comment)} for comment in comments[:6]], "wordCloud": {"positive": [w for w, _ in positive_words] or ["helpful", "great", "love"], "negative": [w for w, _ in negative_words] or ["slow", "confusing", "boring"]}, "trend": trend, "keywords": [w for w, _ in keyword_counts], "gaps": gaps, "prescriptions": prescriptions(engagement, sent, videos)}


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
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify(error="A video title is required."), 400
    try:
        length = max(1, min(240, float(data.get("length", 9))))
        baseline = max(1.0, min(25.0, float(data.get("channelEngagement", 6.2))))
        avg_views = max(100, float(data.get("channelAvgViews", 46500)))
    except (TypeError, ValueError):
        return jsonify(error="Length and channel metrics must be valid numbers."), 400

    category = str(data.get("category", "Other"))
    thumbnail = str(data.get("thumbnail", "Face with expression"))
    hook = str(data.get("hook", "Statement"))
    cta = str(data.get("cta", "None"))
    category_bonus = {"AI/Tech": .65, "Tutorial": .55, "Education": .45, "Review": .30, "Gaming": .20, "Entertainment": .15, "Vlog": -.05, "Other": 0}.get(category, 0)
    thumbnail_bonus = {"Face with expression": .75, "Product shot": .35, "Text only": -.15, "No face": -.35}.get(thumbnail, 0)
    hook_bonus = {"Question": .45, "Statistic": .55, "Story": .20, "Controversial": .30, "Statement": .10}.get(hook, 0)
    cta_bonus = {"Comment": .30, "Watch next": .20, "Subscribe": .10, "Learn more": .05, "None": 0}.get(cta, 0)
    title_bonus = min(1.2, len(words(title)) * .055) + (.4 if any(x in title.lower() for x in ["how", "best", "secret", "tested", "truth"]) else 0)
    length_bonus = .85 if 7 <= length <= 12 else (.35 if 5 <= length <= 18 else -.55)
    rate = max(1.2, min(18.5, baseline + title_bonus + category_bonus + thumbnail_bonus + hook_bonus + cta_bonus + length_bonus - .45))
    uplift = round((rate / baseline - 1) * 100)
    view_factor = max(.45, min(2.1, 1 + uplift / 125))
    recommendations = []
    if thumbnail == "No face": recommendations.append("Test an expressive face or a clear product close-up; both typically improve click intent.")
    if not 7 <= length <= 12: recommendations.append("Aim for a 7–12 minute cut unless the topic needs a deeper tutorial format.")
    if hook == "Statement": recommendations.append("Lead with a precise statistic or an audience question to create a stronger first-15-second hook.")
    if cta == "None": recommendations.append("Add one focused comment CTA near the ending to turn positive sentiment into engagement.")
    recommendations += [f"Frame the title around a specific {category.lower()} outcome, not just the process.", "Show the payoff before the first 12 seconds, then earn the explanation."]
    confidence = min(94, 72 + (8 if data.get("channelAvgViews") else 0) + (5 if category != "Other" else 0))
    return jsonify({"engagement": round(rate, 1), "confidence": confidence, "views48": int(avg_views * .55 * view_factor), "likes48": int(avg_views * .55 * view_factor * rate / 100 * .86), "comments48": int(avg_views * .55 * view_factor * rate / 100 * .12), "uplift": uplift, "summary": "Above channel average" if uplift >= 0 else "Below channel average", "recommendations": recommendations[:3]})

if __name__ == "__main__": app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
