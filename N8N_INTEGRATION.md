# n8n Integration Guide for PokémonKnower

This document explains how to set up n8n workflows to automate features in PokémonKnower.

## Available Webhook Endpoints

### 1. Featured Pokémon Automation

**Endpoint:** `GET/POST https://your-site.com/api/n8n/featured-pokemon`

- **GET**: Returns a random high-stat Pokémon suitable for the hero carousel
- **POST**: Push a specific Pokémon ID to feature

**Use Case**: Daily cron job to update the featured Pokémon on the homepage.

---

### 2. Daily Digest Data

**Endpoint:** `POST https://your-site.com/api/n8n/daily-digest`

Returns data for email newsletters:

- Total Pokémon count
- Trending Pokémon list
- Quiz of the day

**Use Case**: Connect to email service (SendGrid, Mailchimp) for automated newsletters.

---

### 3. AI Story Generation

**Endpoint:** `POST https://your-site.com/api/n8n/generate-story`

**Request Body:**

```json
{
  "pokemon_name": "Charizard",
  "story_type": "origin" // origin, battle, journey
}
```

**Response:** Returns prompt data for AI (OpenAI, Claude) to generate a story.

**n8n Workflow:**

1. HTTP Request to `/api/n8n/generate-story`
2. OpenAI node with the `prompt_template`
3. HTTP Request to `/api/n8n/webhook/story-created` with generated story

---

### 4. User Re-engagement

**Endpoint:** `POST https://your-site.com/api/n8n/user-engagement`

Returns users who haven't logged in for 7+ days.

**Use Case**: Automated "We miss you!" email campaigns.

---

### 5. Story Webhook

**Endpoint:** `POST https://your-site.com/api/n8n/webhook/story-created`

Receives generated stories from AI workflows.

---

## Example n8n Workflow: Daily Featured Pokémon

```
[Schedule Trigger: 9 AM daily]
       ↓
[HTTP Request: GET /api/n8n/featured-pokemon]
       ↓
[Set: Format message]
       ↓
[Twitter/Discord/Slack: Post "Pokémon of the Day"]
```

## Example n8n Workflow: AI Story Generator

```
[Webhook Trigger: "Generate Story"]
       ↓
[HTTP Request: POST /api/n8n/generate-story]
       ↓
[OpenAI: Generate story from prompt_template]
       ↓
[HTTP Request: POST /api/n8n/webhook/story-created]
       ↓
[Slack/Discord: Notify admin of new story]
```

## Setup Instructions

1. **Install n8n**: Self-host or use n8n Cloud
2. **Create Credentials**: Add your site URL as an HTTP credential
3. **Import Workflows**: Use the examples above as templates
4. **Set Environment Variables**:
   - `N8N_WEBHOOK_URL` in your `.env`
   - API keys for OpenAI, SendGrid, etc.

## Security

For production, consider adding API key authentication to n8n endpoints:

```python
@app.before_request
def verify_n8n_api_key():
    if request.path.startswith('/api/n8n/'):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.environ.get('N8N_API_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401
```
