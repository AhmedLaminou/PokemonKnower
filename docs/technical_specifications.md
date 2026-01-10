# Technical Specifications - Pokémon Knower

## 1. System Architecture

The application follows a monolithic architecture with modular components, built on **Flask (Python)**.

### Core Components

- **Web Server**: Flask (handles HTTP requests, routing, and extensions).
- **Database**: SQLite (Development) / PostgreSQL (Production) using SQLAlchemy ORM.
- **AI Engine**:
  - **TensorFlow/Keras**: Local CNN model (`.h5`) for offline/fast image classification (151 original Pokémon).
  - **OpenAI/OpenRouter**: LLM for "Who's That Pokémon?" trivia generation and Storytelling.
  - **VLM (Vision Language Model)**: Fallback for image recognition when local model confidence is low.
- **Frontend**: Server-side rendered HTML (Jinja2) with vanilla CSS (Netflix-style aesthetics) and JavaScript.

## 2. Technology Stack

- **Backend**: Python 3.9+, Flask, SQLAlchemy, Flask-Login, Flask-CORS.
- **AI/ML**: TensorFlow 2.x, LangChain, OpenAI API.
- **Database**: SQLite (default), extensible to PostgreSQL.
- **Frontend**: HTML5, CSS3 (Custom Variables + Glassmorphism), JavaScript (ES6+).
- **Authentication**: Stytch (Magic Links / OAuth) + Local Session Management.

## 3. Database Schema

### Users

- `id`: Integer (PK)
- `email`: String (Unique)
- `stytch_user_id`: String (Auth Provider ID)
- `exp`: Integer (Experience Points)
- `level`: Integer (Calculated from XP)

### Pokemon

- `id`: Integer (PK)
- `name`: String
- `number`: Integer (Pokedex #)
- `types`: String (JSON/List)
- `stats`: JSON (HP, Atk, Def, etc.)

### QuizScore

- `id`: Integer (PK)
- `user_id`: Integer (FK)
- `score`: Integer
- `created_at`: Datetime

## 4. API Endpoints

### Core

- `GET /`: Home page.
- `GET /pokedex`: List/Filter Pokémon.
- `GET /pokemon/<id>`: Detailed view.

### AI Features

- `POST /predict`: Upload image for identification (Local -> VLM Fallback).
- `GET /api/quiz/ai_question`: Generate trivia question via LLM (Auth required).
- `POST /api/stories/generate`: Generate creative story via LLM.

## 5. Security

- **Authentication**: Session-based, backed by Stytch passwordless/OAuth.
- **Route Protection**: `@login_required` decorator for gamification/AI features.
- **Environment**: API keys stored in `.env`, not committed to repo.
