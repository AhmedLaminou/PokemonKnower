# Documentation Index

Welcome to the **Pokémon Knower** documentation. This folder contains detailed specs and guides for the project.

## Available Documents

### 1. [Technical Specifications](technical_specifications.md)

- **Audience**: Developers, Contributors.
- **Content**: System architecture, databases, API contracts, AI model details, and dependencies.
- **Use when**: Debugging backend issues, adding new API endpoints, or understanding the AI pipeline.

### 2. [Cahier des Charges (Requirements)](cahier-des-charges.md)

- **Audience**: Project Managers, Stakeholders, Designers.
- **Content**: Functional requirements, user stories, feature lists, and future roadmap.
- **Use when**: Verifying feature completeness or planning new modules.

## Project Structure Overview

```
PokemonKnower/
├── app.py                 # Main Flask Application Entry Point
├── ai_engine.py           # AI Wrapper (LangChain, Vision, Local Model)
├── models/                # Database Models (SQLAlchemy)
├── static/
│   ├── css/netflix.css    # Main Stylesheet (Premium UI)
│   └── js/netflix.js      # Frontend Logic (Carousel, Voice, UI)
├── templates/             # HTML Templates (Jinja2)
│   ├── home.html          # Landing Page
│   ├── scanner.html       # AR Scanner Interface
│   └── quiz.html          # AI Trivia Game
└── docs/                  # You are here!
```
