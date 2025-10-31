#!/bin/bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DEFAULT_PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | tr '-' '_')
PYTHON_VERSION="3.12"

# Functions
print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}Error:${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Initialize git if needed
init_git() {
    if [ ! -d ".git" ]; then
        print_step "Initializing git repository..."
        git init
        git add .
        git commit -m "Initial commit from python-claude-template"
        print_success "Git repository initialized"
    else
        print_success "Git repository already exists"
    fi
}

install_or_upgrade() {
    local check_cmd="$1"
    local apt_package="${2:-${check_cmd}}"

    # コマンドが存在するか確認
    if ! command -v "${check_cmd}" &> /dev/null; then
        echo "Install ${apt_package}"
        sudo apt-get install -y "${apt_package}"
    else
        echo "Update ${apt_package}"
        sudo apt-get upgrade -y "${apt_package}"
    fi

    return $?
}

# Install font packages if not already installed
install_font_if_missing() {
    local font_package="$1"

    # Check if font package is installed
    if ! dpkg -l | grep -q "^ii  ${font_package}"; then
        sudo apt-get install -y "${font_package}"
        print_success "${font_package} installed"
    else
        print_success "${font_package} already installed"
    fi
}

# Main setup flow
main() {
    echo "🚀 MkDocs Mermaid to Image Plugin Setup"
    echo "======================================="
    echo

    set -e

    # === SYSTEM PREPARATION ===
    sudo apt-get update
    sudo apt-get install -y \
        fonts-noto-cjk \
        fonts-ipafont-gothic \
        fonts-ipafont-mincho \
        fonts-noto-color-emoji \
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libgbm1 \
        libasound2t64

    # # sudo apt-get install -y build-essential make        # build-essential, make (development tools)

    # === GitHub CLI ===
    install_or_upgrade gh

    # === Setup Python Environments ===
    install_or_upgrade pip python3-pip          # pipの導入・更新
    sudo apt-get install -y python3.12-venv     # python3-venvパッケージの導入（仮想環境作成に必要）
    
    # uvをインストール（公式のインストール方法を使用）
    if ! command -v uv &> /dev/null; then
        print_step "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        print_success "uv installed"
    else
        print_success "uv already installed"
    fi
    
    # uvで仮想環境を作成（既存の.venvがある場合はスキップ）
    if [ ! -d ".venv" ]; then
        print_step "Creating virtual environment with uv..."
        uv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists, skipping creation"
    fi
    
    # Pythonバージョンをピン止め
    uv python pin $PYTHON_VERSION
    
    # プロジェクトと全依存関係をインストール
    print_step "Installing project dependencies..."
    uv pip install -e .                         # プロジェクトを開発モード（editable）でインストール
    uv pip install --group dev                  # dev依存関係グループをインストール
    print_success "Dependencies installed"

    # === Setup Node.js Environment ===
    print_step "Setting up Node.js environment..."
    
    # Install or update nvm
    if ! command -v nvm &> /dev/null; then
        print_step "Installing nvm..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
        [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
        print_success "nvm installed"
    else
        print_success "nvm already installed"
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    fi

    # Install Node.js LTS
    print_step "Installing Node.js LTS..."
    # set -e の影響を一時的に無効化してnvmを実行
    set +e
    nvm install --lts
    nvm alias default 'lts/*'
    set -e
    print_success "Node.js LTS installed"

    # Install Mermaid CLI (required for plugin functionality)
    print_step "Installing Mermaid CLI..."
    npm install -g @mermaid-js/mermaid-cli
    print_success "Mermaid CLI installed"

    # === Setup AI Development Tools (Optional) ===
    print_step "Installing AI development tools..."
    npm install -g @anthropic-ai/claude-code@latest
    npm install -g @google/gemini-cli@latest
    print_success "AI tools installed"

    # === Setup Pre-commit Hooks ===
    print_step "Setting up pre-commit hooks..."
    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg
    print_success "Pre-commit hooks installed"

    # === VERIFICATION ===
    print_step "Verifying installation..."
    
    # Run tests to verify plugin functionality
    print_step "Running test suite..."
    uv run pytest tests
    print_success "All tests passed"
    
    # Build documentation to verify MkDocs integration
    print_step "Building documentation..."
    uv run mkdocs build
    print_success "Documentation built successfully"

    # === COMPLETION ===
    echo
    echo "✨ Setup complete!"
    echo
    echo "📦 Installed components:"
    echo "  - Python ${PYTHON_VERSION} virtual environment (uv)"
    echo "  - MkDocs with mermaid-to-svg plugin"
    echo "  - Node.js LTS with Mermaid CLI"
    echo "  - Pre-commit hooks"
    echo "  - AI development tools (Claude Code, Gemini CLI)"
    echo
    echo "🚀 Next steps:"
    echo "  - Run 'make test' to run the test suite"
    echo "  - Run 'make serve' to start the development server"
    echo "  - Run 'make check' to run code quality checks"
    echo
    echo "📚 Documentation: http://127.0.0.1:8000 (after 'make serve')"
    echo
}

# Run main function
main
