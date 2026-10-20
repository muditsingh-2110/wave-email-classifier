# Wave Email Classifier — Complete Setup Guide

Everything you need to go from local Python → live tool in watsonx Orchestrate.

---

## Files in this folder

| File | What it is |
|------|-----------|
| `classify_emails.py` | Core classifier logic (already working) |
| `dummy_emails.json` | 10 test emails |
| `api.py` | Flask wrapper — turns classifier into a REST API |
| `openapi.yaml` | YML file your senior mentioned — describes the API to Orchestrate |
| `classification_results.json` | Output from last local run |

---

## PART 1 — Run locally (already done)

```bash
cd d:\MS\automation\wave_email_agent
python classify_emails.py
```

---

## PART 2 — Start the API

### Step 1 — Install Flask (one time only)

```bash
pip install flask
```

### Step 2 — Start the API server

```bash
python api.py
```

You will see:
```
Wave Email Classifier API is running!
Health check : http://localhost:5000/health
Demo run     : http://localhost:5000/classify/demo
```

### Step 3 — Test it in your browser

Open this URL in Chrome:
```
http://localhost:5000/classify/demo
```

You should see JSON output with all 10 emails classified.

### Step 4 — Test with Postman (optional)

- Method: `POST`
- URL: `http://localhost:5000/classify`
- Body (raw JSON):
```json
{
    "id": "TEST-001",
    "from": "test@gmail.com",
    "subject": "Lift broken",
    "body": "The lift in Tower B is not working since 3 days. Please help urgently."
}
```

---

## PART 3 — Port forwarding with ngrok

Orchestrate is on IBM Cloud. It cannot reach `localhost:5000` on your laptop.
ngrok creates a public URL that forwards to your local API.

### Step 1 — Download ngrok

Go to: https://ngrok.com/download

Create a free account and download ngrok for Windows.

### Step 2 — Connect your ngrok account (one time)

```bash
ngrok config add-authtoken YOUR_AUTHTOKEN_FROM_NGROK_DASHBOARD
```

### Step 3 — Start port forwarding

Open a NEW terminal (keep `api.py` running in the first terminal) and run:

```bash
ngrok http 5000
```

You will see something like:
```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:5000
```

Copy that `https://abc123.ngrok-free.app` URL — you need it in the next step.

### Step 4 — Update openapi.yaml with your ngrok URL

Open `openapi.yaml` and replace this line:
```yaml
  - url: https://YOUR-NGROK-URL.ngrok-free.app
```
with your actual ngrok URL, for example:
```yaml
  - url: https://abc123.ngrok-free.app
```

### Step 5 — Verify it works publicly

Open in browser:
```
https://abc123.ngrok-free.app/classify/demo
```
(use your actual ngrok URL)

You should see the same JSON output as localhost. If yes — your API is live on the internet.

---

## PART 4 — Import into watsonx Orchestrate

### Step 1 — Log in to Orchestrate

Go to your IBM watsonx Orchestrate instance URL and log in.

### Step 2 — Go to Skills / Tools

- Click **Skills** in the left sidebar
  OR
- Click **Tools** depending on your Orchestrate version

### Step 3 — Import the OpenAPI spec

1. Click **Add skill** or **Add tool** or **Import**
2. Select **From file** or **From OpenAPI spec**
3. Upload `openapi.yaml` from this folder
4. Orchestrate will show you 4 operations:
   - `healthCheck`
   - `classifySingleEmail`
   - `classifyBatchEmails`  ← this is the main one
   - `classifyDemoEmails`
5. Select all 4 and click **Add** or **Import**

### Step 4 — Create the Agent

1. Go to **Agents** → **Create agent**
2. Fill in:
   - **Name:** `Wave CRM Email Agent`
   - **Description:** Classifies customer emails into Service Request, Complaint, or General Query for UCHDPL Wave CRM
3. Under **Tools**, add the tools you just imported
4. Under **Instructions**, paste this:

```
You are the Wave CRM Email Agent for UCHDPL real estate.

When a user asks you to classify emails:
- If they give you emails, use the classifyBatchEmails tool
- If they want to see a demo, use the classifyDemoEmails tool
- Always present results clearly showing: email subject, category, priority, and which team it goes to
- Group results by category: Complaints first, then Service Requests, then General Queries
```

5. Click **Save** and then **Deploy** or **Publish**

### Step 5 — Test the agent

In the Orchestrate chat, type:

> *"Run the demo and show me all email classifications"*

The agent will call your Python API through ngrok, get the results, and show them conversationally.

---

## IMPORTANT — Keep these running while testing

You need 3 things running at the same time:

| Terminal | Command | What it does |
|----------|---------|-------------|
| Terminal 1 | `python api.py` | Your Flask API |
| Terminal 2 | `ngrok http 5000` | Port forwarding |
| Browser | Orchestrate | The agent UI |

---

## Quick troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: flask` | Run `pip install flask` |
| ngrok URL not working | Make sure `api.py` is still running in Terminal 1 |
| Orchestrate can't reach API | Check ngrok is running, URL in openapi.yaml is updated |
| `classify_emails not found` | Run `api.py` from inside the `wave_email_agent/` folder |

---

## Summary — what your senior described

| What she said | What it means | File/Tool |
|---------------|--------------|-----------|
| "Make an API" | Wrap Python as a web service | `api.py` |
| "YML file" | Describe the API for Orchestrate | `openapi.yaml` |
| "Port forwarding" | Make localhost reachable from internet | ngrok |
| "Make a tool" | Import OpenAPI into Orchestrate | Orchestrate UI step |
| "Create agent" | Build the agent and attach tools | Orchestrate UI step |
