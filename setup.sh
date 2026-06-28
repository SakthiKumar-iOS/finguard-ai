#!/usr/bin/env bash
# setup.sh
# Purpose: Initialize virtual environment, install requirements, and download NLP models.

# Exit immediately if a command exits with a non-zero status
set -e

echo "Initializing Python 3.13 virtual environment..."
python3.13 -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing requirements..."
pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  .env created from .env.example"
    echo "👉  Open .env and add your GEMINI_API_KEY before running"
    echo "🔑  Get your key at: https://aistudio.google.com/app/apikey"
else
    echo "✅  .env already exists — skipping"
fi

echo "Downloading Spacy English model..."
python -m spacy download en_core_web_sm

echo "Setup complete"
