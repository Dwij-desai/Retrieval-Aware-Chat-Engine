#!/bin/bash

# Load conda into script
source $(conda info --base)/etc/profile.d/conda.sh

ENV_NAME="ai_saas"

echo "🚀 Setting up environment: $ENV_NAME"

# Check if env already exists
if conda env list | grep -q $ENV_NAME; then
    echo "⚠️ Environment already exists. Activating..."
else
    echo "📦 Creating new conda environment..."
    conda create -n $ENV_NAME python=3.11 -y
fi

# Activate environment
conda activate $ENV_NAME

# Verify
echo "✅ Active environments:"
conda info --envs

echo "🐍 Python version:"
python --version

# Install packages (Google-based stack)
echo "📚 Installing dependencies..."

pip install \
langchain \
langchain-google-genai \
langchain-community \
chromadb \
fastapi \
uvicorn \
pypdf \
sentence-transformers \
python-dotenv \
pydantic-settings \
google-generativeai

# Save dependencies
echo "💾 Saving requirements.txt..."
pip freeze > requirements.txt

echo "🎉 Setup complete!"
