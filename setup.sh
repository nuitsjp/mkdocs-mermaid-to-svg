#!/bin/bash

# MkDocs Mermaid to Image Plugin - Setup Script
# This script installs all necessary dependencies

set -e  # Exit on any error

echo "🚀 Setting up MkDocs Mermaid to Image Plugin..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Environment checks passed"

# Install Mermaid CLI
echo "📦 Installing Mermaid CLI..."
if ! command -v mmdc &> /dev/null; then
    npm install -g @mermaid-js/mermaid-cli
    echo "✅ Mermaid CLI installed"
else
    echo "✅ Mermaid CLI already installed ($(mmdc --version))"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "🐍 Installing Python dependencies..."
source .venv/bin/activate

# Upgrade pip in virtual environment
pip install --upgrade pip

# Install dependencies from pyproject.toml
pip install -e .[dev]

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Configure your mkdocs.yml"
echo "3. Run: mkdocs serve"
echo ""
echo "Note: Remember to activate the virtual environment before using the plugin:"
echo "      source .venv/bin/activate"
echo ""
echo "For more information, see: docs/installation.md"
