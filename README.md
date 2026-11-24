# AI Response Quality Evaluator Agent

An intelligent multi-agent platform that uses LLMs as automated judges to evaluate the quality of AI-generated responses across multiple dimensions.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green)
![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Overview

As AI-powered applications become increasingly common, a critical question emerges: **how do you know if your AI is actually giving good answers?**

This platform provides automated, reliable, and explainable evaluation of AI responses using a multi-agent judging pipeline powered by LLMs.

## 🏗️ Architecture

The platform uses **5 specialized judge agents** that evaluate AI responses:

| Agent | Role | What It Evaluates |
|-------|------|------------------|
| **Relevance Judge** | Scores topical alignment | How directly the response addresses the question |
| **Accuracy Judge** | Checks factual correctness | Factual alignment with reference answers |
| **Hallucination Detector** | Flags unsupported claims | Claims not grounded in source documents |
| **Completeness Judge** | Assesses coverage | Whether all aspects of the question are addressed |
| **Verdict Agent** | Aggregates scores | Weighted overall score with consolidated reasoning |

## ✨ Features

- **Single Evaluation**: Submit a question, AI response, and optional reference for instant multi-dimensional scoring
- **Batch Evaluation**: Upload CSV files with question-answer pairs for automated bulk testing
- **Detailed Reasoning**: Not just scores — each dimension includes why that score was assigned
- **Hallucination Detection**: Specific claims flagged as supported, unsupported, or fabricated
- **Scoring Dashboard**: Interactive charts showing quality trends, score distributions, and pass/fail rates
- **Quality Tiers**: Responses classified as Excellent, Good, Fair, Poor, or Failing

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- A free [Groq API key](https://console.groq.com/keys)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd ai-response-validator
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   ```

5. **Run the server**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

6. **Open in browser**
   ```
   http://localhost:8000
   ```

### Deploy to Render (Free)

1. Push your code to GitHub
2. Go to [render.com](https://render.com) and create a new **Web Service**
3. Connect your GitHub repository
4. Render will auto-detect settings from `render.yaml`
5. Add environment variable: `GROQ_API_KEY` = your Groq API key
6. Deploy!

## 📊 Scoring System

Each dimension is scored on a **1-10 scale**:

| Score Range | Quality Tier | Meaning |
|-------------|-------------|---------|
| 9.0 - 10.0 | 🟢 Excellent | Outstanding quality |
| 7.0 - 8.9 | 🔵 Good | High quality with minor issues |
| 5.0 - 6.9 | 🟡 Fair | Acceptable but needs improvement |
| 3.0 - 4.9 | 🟠 Poor | Significant issues |
| 1.0 - 2.9 | 🔴 Failing | Unacceptable quality |

**Weighted scoring formula:**
- Relevance: 25%
- Accuracy: 30%
- Hallucination: 25%
- Completeness: 20%

## 📁 Batch CSV Format

Upload CSV files with these columns:

```csv
question,ai_response,reference_answer
"What is Python?","Python is a programming language.","Python is a high-level interpreted language..."
```

- `question` (required): The question that was asked
- `ai_response` (required): The AI-generated response to evaluate
- `reference_answer` (optional): Reference answer for accuracy/hallucination checking

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/evaluate` | Submit single evaluation |
| GET | `/api/evaluations` | List past evaluations |
| GET | `/api/evaluations/{id}` | Get evaluation details |
| DELETE | `/api/evaluations/{id}` | Delete evaluation |
| POST | `/api/batch/upload` | Upload batch CSV |
| GET | `/api/batch/jobs` | List batch jobs |
| GET | `/api/batch/jobs/{id}` | Get batch job status |
| GET | `/api/batch/jobs/{id}/download` | Download batch results CSV |
| GET | `/api/dashboard/stats` | Dashboard statistics |
| GET | `/api/dashboard/trends` | Score trends |

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, uvicorn
- **LLM**: Groq API (Llama 3.3 70B Versatile)
- **Database**: SQLite (async via aiosqlite)
- **Frontend**: Vanilla HTML/CSS/JS, Chart.js
- **Deployment**: Render Free Tier

## 📄 License

MIT License — feel free to use this for learning and building!
