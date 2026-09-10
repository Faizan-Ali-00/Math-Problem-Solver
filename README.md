# 🧮 Math Helper

An AI-powered math problem solver that reads math questions from images and provides step-by-step solutions with diagrams. Built with Python, Streamlit, and OpenAI.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?logo=openai&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 📸 Image Upload — Snap or upload a photo of any math problem
- 🤖 AI-Powered Solving — Uses OpenAI models to solve problems step-by-step
- 📐 Diagram Generation — Automatically draws relevant diagrams (geometry, graphs, etc.)
- 🎓 Adaptive Difficulty — Explanations tailored to Matric, FSc, or University level
- 📝 LaTeX Output — Clean, properly formatted mathematical notation
- 🌐 Streamlit Web App — Simple, interactive browser-based interface

## 🚀 Demo

Upload an image of a math problem, get a full solution with explanation and diagram.

Input:  Photo of x² + 5x + 6 = 0
Output: Step-by-step factorization + graph of the parabola

## 🛠️ Tech Stack

- Frontend: Streamlit
- AI Model: OpenAI GPT (vision + reasoning)
- Math Rendering: LaTeX
- Diagrams: Matplotlib / Plotly
- Language: Python 3.10+

## 📂 Project Structure

    math-helper/
    ├── app.py              # Streamlit web app (main entry point)
    ├── solver.py           # Core math solving logic
    ├── explainer.py        # AI-powered step-by-step explanations
    ├── diagrams.py         # Diagram generation utilities
    ├── requirements.txt    # Python dependencies
    ├── .env                # API keys (NOT committed)
    ├── .gitignore          # Git ignore rules
    └── README.md

## ⚙️ Installation

### 1. Clone the repository

    git clone https://github.com/Faizan-Ali-00/Math-Problem-Solver.git
    cd Math-Problem-Solver

### 2. Create a virtual environment

    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS / Linux
    python3 -m venv venv
    source venv/bin/activate

### 3. Install dependencies

    pip install -r requirements.txt

### 4. Set up environment variables

Create a `.env` file in the root directory:

    OPENAI_API_KEY=your_openai_api_key_here

Get your API key from https://platform.openai.com/api-keys

## ▶️ Usage

Run the Streamlit app:

    streamlit run app.py

Then open your browser at http://localhost:8501

1. Upload an image of a math problem
2. Select your difficulty level (Matric / FSc / University)
3. Click Solve
4. View the step-by-step solution and diagram

## 🔒 Security Notes

- Never commit your `.env` file — it contains your OpenAI API key
- `.env` is already listed in `.gitignore`
- If you accidentally expose a key, revoke it immediately at https://platform.openai.com/api-keys

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m "Add some AmazingFeature"`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👤 Author

Faizan Ali

- GitHub: https://github.com/Faizan-Ali-00
- Repository: https://github.com/Faizan-Ali-00/Math-Problem-Solver

## ⭐ Show Your Support

If this project helped you, please give it a star on GitHub.

## 🙏 Acknowledgments

- OpenAI — https://openai.com
- Streamlit — https://streamlit.io
- Matplotlib & Plotly — for diagram rendering
