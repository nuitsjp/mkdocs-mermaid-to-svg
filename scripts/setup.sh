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
        fonts-noto-color-emoji

    # # sudo apt-get install -y build-essential make        # build-essential, make (development tools)

    # === GitHub CLI ===
    install_or_upgrade gh

    # === Setup Python Environments ===
    install_or_upgrade pip python3-pip          # pipの導入・更新
    [ ! -d ".venv" ] && python3 -m venv .venv   # Python仮想環境の作成
    source .venv/bin/activate                   # Python仮想環境の起動
    python3 -m pip install --upgrade uv         # uvの導入
    uv python pin $PYTHON_VERSION               # Pythonバージョンのピン止め
    uv add --dev --editable .                   # プロジェクトを開発モード（editable）でインストールし、開発用依存（dev）も追加
    uv sync --all-extras                        # pyproject.toml で定義された全ての追加依存の導入

    # SNAP packages: Modern tools with latest versions
    command -v nvm &> /dev/null || {
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
        [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
    }

    nvm install --lts

    # AI Agent
    sudo npm install -g @anthropic-ai/claude-code@latest
    sudo npm install -g @google/gemini-cli@latest

    # Setup pre-commit
    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg

    # Mermaid CLI local setup (project-specific)
    sudo npm install -g @mermaid-js/mermaid-cli

    # # Version control initialization
    # init_git                    # git: repository initialization if needed

    # # === VERIFICATION ===

    # Plugin functionality tests
    uv run pytest tests             # uv: pytest execution
    uv run mkdocs build             # uv: MkDocs build test

    # === COMPLETION ===
    echo
    echo "✨ Setup complete!"
    echo
}

# Run main function
main
