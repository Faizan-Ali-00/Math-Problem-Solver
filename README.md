<div align="center">
  <img src="logos/numera.svg" width="360" alt="Numera Logo" />
</div>

# 📐 Numera — Solve Any Math Problem

Solve · Learn · Understand. Numera solves equations, explains step-by-step, and reads math problems from photos — built for Matric, Intermediate, and BS students.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-F55036?logo=groq&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-4285F4?logo=google&logoColor=white)
![Cerebras](https://img.shields.io/badge/Cerebras-FF6B00?logo=cerebras&logoColor=white)
![OpenRouter](https://img.shields.io/badge/OpenRouter-6467F2?logo=openrouter&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## 📖 Overview

Numera is a smart math helper that solves algebraic equations, explains every step, and even reads math problems straight from your camera or photo upload. Built with a **multi-provider AI fallback chain**, it never leaves you stuck — if one provider fails, the next one instantly takes over.

Perfect for students who want to **understand** the solution, not just copy it.

## ✨ Features

- 🧮 **Solve equations** — quadratic, linear, and general expressions
- 📖 **Step-by-step explanations** — clear, numbered steps in simple language
- 📷 **Snap & Solve** — take a photo of a math question, get the solution
- 📊 **Auto diagrams** — graphs, circles, triangles, and polygons generated for every problem
- 📚 **History panel** — auto-saves last 50 solved problems
- ⚙️ **Settings panel** — adjustable level, temperature, and token limit
- 🎚️ **Three student levels** — Matric, Intermediate, BS
- 🔗 **Multi-provider fallback** — Groq → Gemini → Cerebras → OpenRouter
- ⚡ **Provider indicator** — shows which model answered each question
- 🌈 **Beautiful UI** — purple/violet gradient, π logo, glassmorphism cards

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Math Engine | SymPy (local, exact answers) |
| AI Chat (Primary) | Groq (openai/gpt-oss-120b) |
| AI Chat (Fallback 1) | Google Gemini Flash |
| AI Chat (Fallback 2) | Cerebras (llama3.1-8b) |
| AI Chat (Fallback 3) | OpenRouter (llama-3.3-70b:free) |
| Vision (Image Solving) | Groq Qwen3.6-27B + Gemini Vision |
| Diagrams | Matplotlib |
| Language | Python 3.10+ |
| Storage | Local JSON (history.json, settings.json) |

## 🔗 Multi-Provider Architecture

Numera uses a **provider chain** so it never fails due to a single provider running out of credits:

🧮 Explanation → 1. Groq (openai/gpt-oss-120b — fastest)
                    ↓ (fails)
                 2. Gemini 2.5 Flash
                    ↓ (fails)
                 3. Cerebras (llama3.1-8b)
                    ↓ (fails)
                 4. OpenRouter (llama-3.3-70b:free)
                    ↓ (fails)
                 ❌ Error

📷 Vision → 1. Groq Qwen3.6-27B (primary)
              ↓ (fails)
           2. Gemini Vision 2.5 Flash
              ↓ (fails)
           3. OpenRouter Qwen-VL
              ↓ (fails)
           ❌ Error

You only need **one** provider key to start, but adding all four means zero downtime.

## 📂 Project Structure

Math-Problem-Solver/
├── app.py                # Main Streamlit app
├── solver.py             # Core math solver (SymPy)
├── explainer.py          # Multi-provider AI explainer
├── diagrams.py           # Matplotlib diagram generators
├── requirements.txt      # Python dependencies
├── history.json          # Auto-generated — solved problems
├── settings.json         # Auto-generated — saved preferences
├── logos/
│   └── numera.svg        # Numera logo (used in README)
├── .gitignore            # Git ignore rules
└── README.md

## ⚙️ Installation (Local)

1. Clone the repository

git clone https://github.com/Faizan-Ali-00/Math-Problem-Solver.git
cd Math-Problem-Solver

2. Create a virtual environment

Windows:
python -m venv venv
venv\Scripts\activate

macOS / Linux:
python3 -m venv venv
source venv/bin/activate

3. Install dependencies

pip install -r requirements.txt

4. Set up your API keys

Create a .env file in the root directory:

GROQ_API_KEY=gsk_your_groq_key_here
GEMINI_API_KEY=AIza_your_gemini_key_here
CEREBRAS_API_KEY=csk_your_cerebras_key_here
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_key_here

You only need GROQ_API_KEY to start. Add the rest for zero downtime.

## 🔑 Getting Free API Keys

| Provider | Free Tier | Get Key |
|----------|-----------|---------|
| Groq (required) | Fast inference, generous free tier | https://console.groq.com/keys |
| Gemini | 15 RPM · 1,500 req/day | https://aistudio.google.com/app/apikey |
| Cerebras | 1M tokens/day · 30 req/min | https://cloud.cerebras.ai/ |
| OpenRouter | 50 req/day · 20+ free models | https://openrouter.ai/keys |

## 🚀 Deployment (Streamlit Cloud)

1. Push to GitHub

git add .
git commit -m "Deploy Numera"
git push origin main

2. Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Click New app
3. Select your repo: Faizan-Ali-00/Math-Problem-Solver
4. Main file path: app.py
5. Click Deploy

3. Add your API keys as Secrets

Important: Never put API keys in app.py on GitHub — they become public. Use Streamlit Secrets instead.

1. Go to share.streamlit.io → your app → ⋮ → Settings
2. Click the Secrets tab
3. Paste your keys:

GROQ_API_KEY = "gsk_your_groq_key_here"
GEMINI_API_KEY = "AIza_your_gemini_key_here"
CEREBRAS_API_KEY = "csk_your_cerebras_key_here"
OPENROUTER_API_KEY = "sk-or-v1-your_openrouter_key_here"

4. Click Save → Reboot app

## ▶️ Usage

Numera has three modes, accessible via tabs:

### 🧮 Solve a Problem
1. Enter an equation or expression (e.g. `x² - 5x + 6 = 0`)
2. Click **Solve**
3. Get the answer, step-by-step explanation, and a diagram

### 📖 Understand a Definition
1. Enter a math term (e.g. `derivative`, `matrix`, `standard deviation`)
2. Click **Explain**
3. Get a full explanation with worked example and diagram

### 📷 Snap & Solve
1. Take a photo or upload an image of a math question
2. Click **Solve from Image**
3. Get the answer, read from the image, with step-by-step solution

## 🎛️ Settings

Open the ⚙️ Settings tab in the sidebar to configure:

| Setting | Options | Default |
|---------|---------|---------|
| Level | Matric / Intermediate / BS | Matric |
| Temperature | 0.0 – 1.0 | 0.3 |
| Max Tokens | 500 – 3000 | 1500 |

Click **Save Settings** to persist them. Click **Reset to Defaults** to restore original values.

## 📚 History

Every problem you solve is automatically saved in the 📚 History tab (up to the last 50). Each entry includes:

- 🕐 Timestamp
- 📝 Original question
- ✅ Answer preview
- 🎚️ Student level

You can **View**, **Delete** individual entries, or **Clear All** at once.

## 🎨 UI Highlights

- π **in a circle logo** — purple/violet/pink gradient, glowing
- 🌈 **Modern gradient** — cool, elegant, distraction-free
- 💬 **Glassmorphism cards** — soft transparency, purple borders
- 📊 **Auto diagrams** — Matplotlib graphs embedded inline
- ⚡ **Provider badge** — shows which AI model answered
- 📌 **Sidebar** — three tabs: Solve, History, Settings

## 🔒 Security Notes

- Never commit .env to GitHub
- Always use Streamlit Secrets for deployed apps
- Revoke keys immediately if accidentally exposed
- Store each provider's key separately for easy rotation
- On Streamlit Cloud, history.json is wiped on reboot

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: git checkout -b feature/AmazingFeature
3. Commit your changes: git commit -m "Add some AmazingFeature"
4. Push to the branch: git push origin feature/AmazingFeature
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👤 Author

Faizan Ali
GitHub: https://github.com/Faizan-Ali-00
Repository: https://github.com/Faizan-Ali-00/Math-Problem-Solver

## ⭐ Show Your Support

If this project helped you, please give it a star on GitHub — it means a lot!

## 🙏 Acknowledgments

Groq — https://groq.com
Google Gemini — https://ai.google.dev
Cerebras — https://cerebras.ai
OpenRouter — https://openrouter.ai
Streamlit — https://streamlit.io
SymPy — https://sympy.org
