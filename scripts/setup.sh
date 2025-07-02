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

install_update_npm() {
    print_step "Installing/updating Node.js and npm to latest available versions..."

    # Install/update Node.js via snap (includes npm)
    print_step "Installing/updating Node.js via snap..."
    # Remove existing snap node if present
    sudo snap remove node 2>/dev/null || true
    # Install latest LTS
    sudo snap install node --classic
    print_success "Node.js $(node -v) installed/updated via snap"

    # Verify installation
    if ! command -v npm &> /dev/null; then
        print_error "Failed to install npm with Node.js snap package."
        exit 1
    fi
    print_success "npm installed/updated ($(npm --version)), Node.js $(node -v)"
}

install_update_github_cli() {
    print_step "Installing/updating GitHub CLI to latest version..."
    sudo apt-get update
    sudo apt-get install -y gh

    # Verify installation
    if ! command -v gh &> /dev/null; then
        print_error "Failed to install GitHub CLI via apt."
        exit 1
    fi

    print_success "GitHub CLI installed/updated successfully ($(gh --version | head -n1))"
    if ! gh auth status &> /dev/null; then
        print_step "Please run 'gh auth login' to authenticate with GitHub after setup completes."
    fi
}

install_puppeteer_dependencies() {
    print_step "Installing Puppeteer dependencies for Chrome browser..."

    # Install Chrome browser which includes all necessary dependencies
    if ! command -v google-chrome &> /dev/null; then
        print_step "Installing Google Chrome (includes all Puppeteer dependencies)..."
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
        echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
        sudo apt-get update
        sudo apt-get install -y google-chrome-stable
        print_success "Google Chrome installed successfully"
    else
        print_success "Google Chrome already installed"
    fi

    # Alternative: Install chromium as fallback if Google Chrome fails
    if ! command -v google-chrome &> /dev/null && ! command -v chromium-browser &> /dev/null; then
        print_step "Installing Chromium browser as fallback..."
        sudo apt-get install -y chromium-browser
        print_success "Chromium browser installed successfully"
    fi
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

# Run initial tests
run_tests() {
    print_step "Running initial tests..."

    if uv run pytest tests/ -v; then
        print_success "All tests passed!"
    else
        print_warning "Some tests failed. Check test implementation."
    fi
}

# Test plugin installation
test_plugin() {
    print_step "Testing plugin installation..."

    if uv run python -c "from mkdocs_mermaid_to_image.plugin import MermaidToImagePlugin; print('Plugin import successful')"; then
        print_success "Plugin can be imported"
    else
        print_error "Plugin import failed"
        exit 1
    fi

    # Test MkDocs plugin recognition
    if uv run python -c "from importlib.metadata import entry_points; eps = entry_points(); found = [ep.name for ep in eps.select(group='mkdocs.plugins') if 'mermaid' in ep.name]; print(f'Found plugins: {found}')"; then
        print_success "Plugin entry point registered"
    else
        print_warning "Plugin entry point registration issue"
    fi
}

# Test MkDocs build
test_mkdocs() {
    print_step "Testing MkDocs build..."

    if uv run mkdocs build --verbose; then
        print_success "MkDocs build successful"
    else
        print_warning "MkDocs build failed, check configuration"
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

# Main setup flow
main() {
    echo "🚀 MkDocs Mermaid to Image Plugin Setup"
    echo "======================================="
    echo

    set -e

    # === SYSTEM PREPARATION ===
    # sudo apt-get update
    # sudo apt-get install -y fonts-noto-cjk fonts-ipafont-gothic fonts-ipafont-mincho fonts-noto-color-emoji
                                                        # fonts-noto-cjk, fonts-ipafont-* (CJK font support)
    # sudo apt-get install -y build-essential make        # build-essential, make (development tools)

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

    # APT packages: System tools and development dependencies
    # install_puppeteer_dependencies # Puppeteer Chrome browser dependencies

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

    # === PROJECT SETUP ===

    # Mermaid CLI local setup (project-specific)
    sudo npm install -g @mermaid-js/mermaid-cli

    # # Version control initialization
    # init_git                    # git: repository initialization if needed

    # # === VERIFICATION ===

    # # Plugin functionality tests
    # test_plugin                 # uv: import test, entry point verification
    # run_tests                   # uv: pytest execution
    # test_mkdocs                 # uv: MkDocs build test

    # # === COMPLETION ===
    # echo
    # echo "✨ Setup complete!"
    # echo
    # echo "Next steps:"
    # echo "1. Authenticate with services:"
    # echo "   gh auth login         # GitHub CLI authentication"
    # echo "   claude auth           # Claude Code authentication"
    # echo "   gemini auth           # Gemini CLI authentication"
    # echo "2. Initialize project via \`/initialize-project\` via Claude Code"
    # echo "3. Set up branch protection (optional):"
    # echo "   gh repo view --web  # Open in browser to configure"
    # echo "4. Start developing! 🎉"
    # echo
    # echo "Development commands:"
    # echo "  uv run mkdocs serve    # Start development server"
    # echo "  uv run mkdocs build    # Build documentation"
    # echo "  uv run pytest         # Run tests"
    # echo "  make pre-commit        # Run pre-commit checks"
    # echo
    # echo "Quality assurance:"
    # echo "  make test              # Run tests"
    # echo "  make format            # Format code"
    # echo "  make lint              # Lint code"
    # echo "  make typecheck         # Type check"
    # echo "  make check             # Run quality checks"
    # echo "  make check-security    # Run security checks"
    # echo "  make check-all         # Run all checks"
    # echo "  make help              # Show all available commands"
    # echo
    # echo "Plugin development:"
    # echo "  uv add <package>       # Add dependency"
    # echo "  make pr                # Create pull request"
    # echo "  make issue-bug         # Create bug report"
    # echo "  make issue-feature     # Create feature request"
    # echo "  make issue-claude      # Create Claude Code collaboration issue"
    # echo "  make issue             # Create issue (template selection)"
    # echo
}

# Run main function
main
