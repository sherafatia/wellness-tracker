# Wellness Tracker

## Overview

A prototype wellness tracking app that collects daily self-reports through questionnaires and multiple-choice inputs, then generates a personalized wellness score. Built to explore how off-the-shelf large language models (LLMs) can transform subjective symptom narratives into structured, clinically relevant insights. This repository serves as an open prototype for developing tools that bridge patient self-reporting and actionable wellness metrics.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. (Optional) Add your OpenAI API key to `.env` for enhanced AI insights

4. Run the application:
```bash
python app.py
```

5. Open http://localhost:5000 in your browser

## Features

- **Daily Self-Reports**: Interactive questionnaires with multiple-choice inputs
- **Wellness Score**: Personalized scoring algorithm based on mood, energy, sleep, and stress
- **AI Insights**: LLM-powered analysis of symptom narratives
- **Progress Tracking**: Historical data and trend analysis
- **User-Friendly Interface**: Responsive web interface with real-time feedback

## API Endpoints

- `POST /api/users` - Create a new user
- `POST /api/users/{id}/reports` - Submit daily wellness report
- `GET /api/users/{id}/reports` - Get wellness reports
- `GET /api/users/{id}/wellness-summary` - Get wellness summary and trends

## Technology Stack

- **Backend**: Flask, SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Database**: SQLite (easily configurable to PostgreSQL/MySQL)
- **AI Integration**: Ready for OpenAI API integration

## Future Enhancements

- Advanced LLM integration for deeper symptom analysis
- Data visualization with charts and trends
- Mobile app development
- Integration with wearable devices
- Multi-user support with authentication
