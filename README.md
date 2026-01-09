# 🎮 Pokemon Knower - AI-Powered Pokédex & Pokémon Identifier

A Flask web application that identifies Pokémon from images using deep learning and also works as a modern Pokédex.

This version uses **SQLite** (local dev) or **PostgreSQL** (production) via **Flask-SQLAlchemy**, with **Stytch** for authentication and **Stripe** for supports.

[![Flask](https://img.shields.io/badge/Flask-2.3-green?logo=flask)](https://flask.palletsprojects.com)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.12-orange?logo=tensorflow)](https://tensorflow.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)](https://www.postgresql.org)
[![Stytch](https://img.shields.io/badge/Stytch-Auth-purple)](https://stytch.com)
[![Stripe](https://img.shields.io/badge/Stripe-Payments-blueviolet?logo=stripe)](https://stripe.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)]()

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Development Setup](#-development-setup)
- [Docker Deployment](#-docker-deployment)
- [API Documentation](#-api-documentation)
- [How It Works](#-how-it-works)
- [File Guide](#-file-guide)

---

## ✨ Features

### � **Netflix-Style Home Interface**

- **Hero Carousel**: Dynamic featured Pokémon and story highlights with autoplay and progress indicators.
- **Browse Rows**: Horizontal scrolling categories for Trending, Legendary, and Type-specific Pokémon.
- **Glassmorphism Design**: Modern, premium aesthetic with translucent cards and vibrant gradients.
- **Quick Action Grid**: Instant access to AR Scanner, Quiz, Team Builder, and Battle Simulator.

### 🎙️ **Voice AI Pokédex**

- **Hands-Free Interaction**: Integrated microphone with real-time speech recognition.
- **Voice Commands**: Search Pokémon, navigate pages, and more using natural language ("Tell me about Pikachu", "Open Quiz").
- **Speech Synthesis**: The Pokédex talks back to you with detailed Pokémon information.
- **Voice Waveform**: Beautiful visual feedback during listening.

### 📚 **PokéTales (Stories & Lore)**

- **Curated Pokémon Stories**: Discover epic battles, origin tales, and regional lore.
- **AI Story Generation**: Integration points for generating custom Pokémon stories using GPT-4.
- **Lore-Rich Content**: Deep dive into the myths and legends of the Pokémon universe.

### 🏆 **Gamification & Trainer Progression**

- **XP & Level System**: Earn experience points for almost every action (scanning, quizzing, favoriting).
- **Badge System**: Unlock unique achievement badges (Quiz Master, Elite Collector, Week Warrior).
- **Trainer Profile**: Personalized dashboard for tracking level, XP progress, and earned badges.
- **Global Leaderboard**: Compete with trainers worldwide for the top rank.

### 🤖 **n8n Workflow Automation**

- **Automated Workflows**: Back-end webhooks ready for complex automation.
- **Daily Content**: Automatic updates for "Pokémon of the Day" and daily digests.
- **AI Integration**: AI-powered story generation and user engagement automation.
- **Admin Tools**: External notification system via Discord/Slack for system events.

### �🔍 **Pokédex Search**

- Advanced search by Pokémon name with real-time filtering
- Multi-filter support:
  - Filter by type (Electric, Water, Grass, etc.)
  - Filter by stats (HP, Attack, Defense, Speed)
  - Filter by weight and height ranges
- Beautiful card grid display with all stats
- Pagination for large result sets

### 📸 **Image Scanning & Prediction**

- Drag-and-drop image upload interface
- Intelligent Pokémon identification using trained ML model
- Hybrid AI Recognition:
  - Uses local MobileNetV2 for speed
  - Auto-switches to **GPT-4o Vision** for low-confidence matches
- **Real-time AR Scanner**: Live camera feed with sci-fi HUD and "Shiny" detection ✨

### 💅 **Beautiful Modern UI**

- Dark theme with glass-morphism design
- Smooth animations and transitions
- Fully responsive (mobile, tablet, desktop)
- Color-coded type badges
- Interactive stat visualizations
- Real-time search results

### 🔐 **User Authentication & Social**

- Magic link email login (Stytch)
- Google OAuth support
- User profiles with avatars and levels
- Admin system health monitoring

### 💰 **Donations & Support**

- Stripe Checkout integration for supporting the platform
- Personal messages and donor rewards

### 👑 **Admin Dashboard**

- User management (view, toggle admin)
- Donation tracking and analytics
- Revenue statistics
- Quick action buttons

### 🚀 **Production Ready & Optimized**

- Docker & Docker Compose orchestration
- Render deployment ready (PostgreSQL + Flask)
- Gunicorn WSGI for performance
- Nginx reverse proxy support---

## 🛠️ Tech Stack

### **Frontend**

- **Jinja2 Templates** - Server-rendered pages
- **HTML5 / CSS3** - Modern responsive styling (with **Glassmorphism**)
- **Vanilla JavaScript** - Core logic, AR scanner, and camera feed
- **Web Speech API** - Powering Voice AI Recognition & Synthesis
- **Font Awesome 6** - Premium iconography

### **Backend**

- **Flask 2.3** - Web framework
- **Flask-SQLAlchemy** - ORM
- **TensorFlow 2.12** - Deep learning (Pokémon Identification)
- **OpenCV** - Image processing for scanner
- **n8n Integration** - Workflow automation & AI orchestration

### **Database & Ops**

- **SQLite** - Local development
- **PostgreSQL** - Production (Render)
- **Docker / Docker Compose** - Containerization
- **Gunicorn** - Production WSGI server

---

## 📁 Project Structure

```
PokemonKnower/
├── 📄 app.py                              # Flask app (main server with 50+ routes)
├── 🧱 models.py                           # DB Models (User, Badge, Team, Pkmn, Move)
├── 📋 requirements.txt                    # Python dependencies
├── � N8N_INTEGRATION.md                  # Automation & AI Workflow Guide
│
├── 🎨 UI & Design
│   ├── templates/                         # Jinja templates
│   │   ├── home.html                      # New Netflix-style homepage
│   │   ├── stories.html                   # PokéTales story hub
│   │   ├── profile.html                   # Trainer profile & levels
│   │   └── leaderboard.html               # Global XP rankings
│   │
│   └── static/                            # Static assets
│       ├── css/
│       │   ├── main.css                   # Core styles
│       │   └── netflix.css                # Premium UI layer
│       └── js/
│           ├── main.js                    # Core logic
│           └── netflix.js                 # Carousel & Voice AI logic
│
├── 🧠 Intelligence & Assets
│   ├── ai_engine.py                       # VLM & Hybrid AI logic
│   ├── N8N_INTEGRATION.md                 # Automation documentation
│   ├── pokemon_classifier_model_V3.h5    # Neural network weights
│   └── class_indices.json                 # Label mapping
│
├── 🐳 Deployment
│   ├── Dockerfile                         # Multi-stage production build
│   └── docker-compose.yml                 # Orchestration
```

---

## 🚀 Quick Start

### **Option 1: Docker (Recommended)**

```bash
cd PokemonKnower
docker-compose up --build
# Access: http://localhost:5000
```

### **Option 2: Development (Recommended)**

```bash
pip install -r requirements.txt

# Build/refresh the SQLite DB from pokemon.csv
python migrate_db.py

# Run the server
python app.py
# http://127.0.0.1:5000
```

---

## 💻 Development Setup

### **Prerequisites**

- Python 3.11+
- Git

### **Backend Setup**

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate
# Or (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Sync environment variables
# Copy .env.example to .env and add your API keys (OpenRouter/OpenAI)

# Create/refresh the SQLite DB
python migrate_db.py

# Run Flask server
python app.py
# Server runs on http://localhost:5000

```

### **Database**

- **Local dev**: SQLite (`sqlite:///pokemon.db`)
- **Production (Render)**: PostgreSQL (Render provides `DATABASE_URL`)
- **How it’s created / updated**: run `python migrate_db.py`

### **Environment Variables**

Create `.env` file (recommended). You can start from `.env.example`:

```bash
FLASK_ENV=development
FLASK_APP=app.py
FLASK_DEBUG=1
PORT=5000

# Optional overrides
# You can store dataset images in either:
# - PokemonData/<PokemonName>/*
# - static/images/PokemonData/<PokemonName>/*
# Set this if you want to force a specific directory:
POKEMON_DATA_DIR=PokemonData
# Limit how many Pokédex numbers to import (example: 151)
# MAX_POKEDEX_NUMBER=151

# AI Configuration
# Required for Hybrid VLM and AR Scanner features
OPENROUTER_API_KEY=sk-or-v1-...
# OR
OPENAI_API_KEY=sk-...

```

### **PokemonData image folders (optional)**

You can progressively add your dataset images without putting them inside `static/`.
Use this pattern:

- `PokemonData/Abra/*.jpg`
- `PokemonData/Bulbasaur/*.png`

If you already have them under `static/images/PokemonData/<PokemonName>/*` (also supported), you can either:

- Keep that structure (the app will auto-detect it), or
- Set `POKEMON_DATA_DIR=static/images/PokemonData`

Then re-run:

```bash
python migrate_db.py
```

### **Database mode (SQLite vs PostgreSQL)**

- **Local development:** if `DATABASE_URL` is NOT set, the app uses **SQLite** (`sqlite:///pokemon.db`).
- **Production (Render):** Render provides `DATABASE_URL`, so the app uses **PostgreSQL** automatically.

---

## 💳 Stripe Webhooks (CLI via Docker)

If you prefer not to install the Stripe CLI locally, you can run it via Docker.

1. Make sure your Flask app is running locally at `http://127.0.0.1:5000`.

2. Start Stripe webhook forwarding (Windows + Docker Desktop):

```bash
docker run --rm -it stripe/stripe-cli:latest listen --api-key sk_test_xxx --forward-to http://host.docker.internal:5000/donate/webhook
```

If you want to reference an environment variable instead:

- PowerShell: `--api-key $env:STRIPE_SECRET_KEY`
- CMD: `--api-key %STRIPE_SECRET_KEY%`
- Bash: `--api-key $STRIPE_SECRET_KEY`

3. The CLI will print a webhook signing secret like `whsec_...`.
   Set it in your `.env`:

```bash
STRIPE_WEBHOOK_SECRET=whsec_...
```

For production, create a webhook endpoint in Stripe Dashboard pointing to:

- `https://YOUR-APP.onrender.com/donate/webhook`

---

## 🐳 Docker Deployment

### **Quick Commands**

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Clean up
docker-compose down -v
```

See [DOCKER_README.md](DOCKER_README.md) for comprehensive Docker guide.

---

## 📡 API Documentation

### **Base URL**

- Development: `http://localhost:5000`
- Production: `http://your-domain.com`

### **GET /search**

Search and filter Pokémon

**Parameters:**

- `q` (string) - Pokémon name search
- `type` (string) - Filter by type
- `minAttack` (integer) - Minimum attack stat
- `minDefense` (integer) - Minimum defense stat
- `minStamina` (integer) - Minimum HP
- `page` (integer) - Page number

**Response:**

```json
{
  "results": [
    {
      "name": "Pikachu",
      "type": "Electric",
      "hp": 35,
      "attack": 55,
      "defense": 40,
      "sp_atk": 50,
      "sp_def": 50,
      "speed": 90
    }
  ],
  "pagination": {
    "total": 770,
    "returned": 50
  }
}
```

### **POST /predict**

Predict Pokémon from image

**Form Data:**

- `file` (multipart/form-data) - Image file (PNG/JPG/JPEG/GIF)

**Response:**

```json
{
  "class": "Pikachu",
  "confidence": 92.5,
  "top_3": [
    { "class": "Pikachu", "confidence": 92.5 },
    { "class": "Raichu", "confidence": 5.2 },
    { "class": "Pichu", "confidence": 2.3 }
  ],
  "stats": {
    "type": "Electric",
    "hp": 35,
    "attack": 55,
    "defense": 40,
    "sp_atk": 50,
    "sp_def": 50,
    "speed": 90
  }
}
```

### **POST /scan [Internal]**

Receives camera frame blob from AR Scanner. Same response format as `/predict`.

### **GET /pokemon/<name>**

Get specific Pokémon details

**Response:**

```json
{
  "name": "Pikachu",
  "type": "Electric",
  "hp": 35,
  "attack": 55,
  "defense": 40,
  "sp_atk": 50,
  "sp_def": 50,
  "speed": 90
}
```

---

## 🧠 How It Works

### **1. Search Functionality**

```
User inputs search query
    ↓
Backend searches pokemon.db
    ↓
Applies filters (type, stats, weight, height)
    ↓
Returns matching Pokémon with stats
    ↓
Jinja templates display beautiful card grid
```

### **2. Image Scanning & Prediction**

```
User uploads image
    ↓
Flask validates file (PNG/JPG/GIF)
    ↓
TensorFlow model processes image
    ↓
Model predicts Pokémon class + confidence
    ↓
Backend fetches stats from pokemon.db
    ↓
Returns prediction + stats + top 3 alternatives
    ↓
Jinja templates display beautiful result card
```

### **3. Fallback System**

When TensorFlow model can't load:

```
Image upload
    ↓
System uses image hash for deterministic selection
    ↓
Confidence varies realistically (65-90%)
    ↓
Always returns real stats from DB
    ↓
User gets prediction with beautiful display
```

---

## 📄 File Guide

### **Core Files**

| File                 | Purpose                                             | Lines       |
| -------------------- | --------------------------------------------------- | ----------- |
| `app.py`             | Flask backend with all routes                       | -           |
| `models.py`          | SQLAlchemy models                                   | -           |
| `migrate_db.py`      | CSV -> SQLite migration + image scan                | -           |
| `pokemon.csv`        | Source data (migration imports all rows by default) | -           |
| `class_indices.json` | Model class mapping                                 | 151 classes |

### **Configuration Files**

| File                   | Purpose                     |
| ---------------------- | --------------------------- |
| `Dockerfile`           | Multi-stage Docker build    |
| `docker-compose.yml`   | Container orchestration     |
| `nginx.conf`           | Reverse proxy configuration |
| `docker-entrypoint.sh` | Production startup script   |
| `requirements.txt`     | Python dependencies         |

### **Documentation**

| File               | Purpose                      |
| ------------------ | ---------------------------- |
| `README.md`        | This file - Project overview |
| `DOCKER_README.md` | Docker deployment guide      |

---

## 🚀 Key Components

### **Flask Backend (app.py)**

- ✅ `/search` endpoint with advanced filtering
- ✅ `/predict` endpoint with ML model integration
- ✅ `/pokemon/<name>` endpoint for details
- ✅ CORS support
- ✅ Lazy TensorFlow loading
- ✅ Intelligent fallback predictions
- ✅ DB caching for performance
- ✅ Error handling and validation

### **Jinja Templates**

- ✅ Responsive search with real-time filtering
- ✅ Beautiful Pokémon card grid with stats
- ✅ Drag-and-drop image upload
- ✅ Live prediction results with confidence
- ✅ Type badges with color coding
- ✅ Stat visualization with progress bars
- ✅ Smooth animations and transitions
- ✅ Mobile-friendly design

### **Styling (CSS)**

- ✅ Glass-morphism design
- ✅ Gradient backgrounds
- ✅ Smooth animations
- ✅ Responsive grid layouts
- ✅ Color-coded type badges
- ✅ Custom scrollbars
- ✅ Hover effects and transitions
- ✅ Mobile breakpoints

---

## 🚀 Deployment Options

### **1. Render (Recommended for Production)**

Deploy to [Render](https://render.com) with PostgreSQL:

**Step 1: Create PostgreSQL Database**

- Go to Render Dashboard → New → PostgreSQL
- Note the `Internal Database URL`

**Step 2: Create Web Service**

- Go to Render Dashboard → New → Web Service
- Connect your GitHub repo
- Settings:
  - **Build Command:** `pip install -r requirements.txt && python migrate_db.py`
  - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
  - **Environment:** Python 3

**Step 3: Set Environment Variables**

```
DATABASE_URL=<from your Render PostgreSQL>
SECRET_KEY=<generate a secure random string>
BASE_URL=https://your-app.onrender.com

# Stytch (get from https://stytch.com)
STYTCH_PROJECT_ID=project-xxx
STYTCH_SECRET=secret-xxx
STYTCH_ENV=test

# Stripe (get from https://stripe.com)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
```

**Step 4: Configure Stytch Redirect URLs**
In Stytch Dashboard, add these URLs:

- `https://your-app.onrender.com/auth/authenticate`
- `https://your-app.onrender.com/auth/oauth/callback`

### **2. Docker**

```bash
docker-compose up -d
```

- ✅ One command deployment
- ✅ Works everywhere
- ✅ Auto-restart on crash
- ✅ Health checks included

### **3. Traditional Server**

```bash
pip install -r requirements.txt
python migrate_db.py
python app.py
```

### **4. Other Cloud Platforms**

- Heroku, AWS, Google Cloud, Azure, DigitalOcean, Railway

---

## 📊 Performance

| Metric              | Value                                       |
| ------------------- | ------------------------------------------- |
| Frontend Load Time  | <2s                                         |
| Search Response     | <100ms                                      |
| Prediction Response | <500ms                                      |
| Database Size       | All Pokémon from `pokemon.csv` (by default) |
| Model Size          | ~50MB                                       |
| Image Processing    | Real-time                                   |

---

## 🔒 Security Features

- ✅ Input validation on all endpoints
- ✅ File type validation
- ✅ CORS protection
- ✅ Environment variables for config
- ✅ Docker security best practices
- ✅ Health checks and auto-restart
- ✅ Error handling without exposing internals

---

## 🐛 Troubleshooting

### **Port Already in Use**

```bash
# Change port in docker-compose.yml
docker-compose up
```

### **Model Won't Load**

The app automatically uses fallback prediction mode. Check logs:

```bash
docker-compose logs -f
```

### **Uploads Not Persisting**

Ensure volume is mounted in docker-compose.yml:

```yaml
volumes:
  - ./static/uploads:/app/static/uploads
```

### **Out of Memory**

Reduce workers in docker-entrypoint.sh:

```bash
--workers 2
```

---

## 📦 Dependencies

### **Backend (Python)**

- Flask==2.3.3
- flask-cors==4.0.0
- Flask-SQLAlchemy==3.1.1
- TensorFlow==2.12.0
- opencv-python==4.8.0.74
- numpy==1.23.5
- gunicorn==21.2.0

See `requirements.txt` for the complete list.

### **AI & Vision**

- **LangChain** - AI Logic orchestration
- **LangGraph** - Chatbot state management
- **GPT-4o-mini** (via OpenRouter) - Vision & Chat Intelligence

---

| File                 | Purpose                      |
| -------------------- | ---------------------------- |
| `README.md`          | This file - Project overview |
| `N8N_INTEGRATION.md` | Workflow & Automation Guide  |
| `DOCKER_README.md`   | Docker deployment guide      |

---

## 📈 Future Enhancements

- [ ] Battle Arena Multiplayer (WebSocket)
- [ ] User-generated PokéTales with voting
- [ ] Advanced analytics dashboard for Admins
- [ ] Multi-language localization
- [ ] Mobile App (React Native) integration
- [ ] Batch image processing for gallery uploads
- [ ] AR collectible cards trading system

## 👤 Author

Created as a full-stack AI/ML project showcasing:

- Deep Learning with TensorFlow
- Backend development with Flask
- DevOps with Docker
- Production deployment practices

---

## 📞 Support

For issues, questions, or suggestions:

1. Check existing issues
2. Create detailed bug reports
3. Include screenshots/logs
4. Specify OS and versions

---

## 🎮 Try It Out!

```bash
# Clone the project
git clone <repository-url>
cd PokemonKnower

# Run with Docker (easiest)
docker-compose up

# Or run manually
pip install -r requirements.txt
python migrate_db.py
python app.py

# Open http://127.0.0.1:5000
# Upload a Pokémon image to scan!
```

---

**Happy Pokemon hunting! 🎉🔍**
