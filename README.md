# Bot Deployment Guide

## 📋 Prerequisites
Before deployment, ensure you have:
1. Installed required packages:
```bash
pip install -r requirements.txt
```
API Keys stored in .env file:
```bash
OPENAI_API_KEY=your_openai_api_key
GOOGLE_CSE_ID=your_google_id_key
GOOGLE_API_KEY=your_google_api_key
ANTHROPIC_API_KEY=your_claude_api_key
ELEVENLABS_API_KEY=tyour_elevenlabs_api_key
API_KEY=your_api_key
```
🤖 Creating a Bot Instance
Available bot templates:
```bash
QuizMaster.py

MagicPrompt.py

LinkedInWizard.py
```
🚀 Running the Application
Start the Streamlit server:
```bash
streamlit run app_name.py
```
✔️ Verification
Check Streamlit installation:
```bash
streamlit --version
```
Install Streamlit if missing:
```bash
pip install streamlit
```
Install all packages used:
```bash
pip install -r requirements.txt
```

