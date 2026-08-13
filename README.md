# The Content Surgeon

The Content Surgeon is a dark-mode YouTube analytics dashboard built for creators planning their next upload. It turns recent channel performance and comment signals into actionable prescriptions, content-gap ideas, and a pre-publish engagement prediction.

![Dashboard preview](https://placehold.co/1200x630/080b13/ffffff?text=The+Content+Surgeon)

## What it does

- Analyses a public YouTube channel from a URL, `@handle`, or channel ID.
- Pulls the latest 10 videos, their public metrics, and available comments through YouTube Data API v3.
- Calculates comment sentiment, shows a sentiment trend and positive/negative language signals.
- Produces five content-gap opportunities and five actionable publishing prescriptions.
- Includes **The Crystal Ball**, an instant pre-upload engagement predictor based on title and duration.
- Degrades gracefully to deterministic demo data when no API key is configured, so the product is always demo-ready.

## Run locally

Requirements: Python 3.10+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell
pip install -r requirements.txt
python app.py
```

Open [http://localhost:5000](http://localhost:5000).

## Enable live YouTube data

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable **YouTube Data API v3**.
3. Create a restricted API key with access to that API.
4. Set the key before starting the app:

```powershell
$env:YOUTUBE_API_KEY="your_key_here"
python app.py
```

Paste a public channel URL or `@handle` in the dashboard and select **Analyze**. The application uses the API key only on the server; it is never sent to the browser. Comment availability is determined by the channel's public settings and YouTube quota limits.

## Deploy

This repository includes `vercel.json` from the prior project setup, but this Flask app is readily deployable to Render, Railway, Fly.io, or any Python host. Use:

```bash
gunicorn app:app
```

Configure `YOUTUBE_API_KEY` as a host-side environment variable. Never commit it.

## Architecture

The project is deliberately compact for hackathon use:

- `app.py` – Flask service, YouTube integration, lightweight lexical sentiment, channel analysis, and prediction endpoint.
- `index.html`, `style.css`, `script.js` – responsive single-page dashboard with no build step.
- `requirements.txt` – production dependencies.

For a production multi-user version, move channel snapshots to Supabase/Postgres, authenticate users with Supabase Auth, and use OAuth consent where user-private data or channel management is required. Public channel analytics work with a server-side API key.
