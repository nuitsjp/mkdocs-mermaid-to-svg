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

# Detect shell and set rc_file
rc_file="~/.bashrc"
if [[ "$SHELL" == "/bin/zsh" ]]; then
    rc_file=~/.zshrc
elif [[ "$SHELL" == "/bin/bash" ]]; then
    rc_file=~/.bashrc
elif [[ "$SHELL" == "/bin/fish" ]]; then
    rc_file=~/.config/fish/config.fish
else
    print_error "Failed to detect shell. Please set rc_file manually."
fi

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

# Check if uv is installed
check_uv() {
    if ! command -v uv &> /dev/null; then
        print_step "uv is not installed. Installing uv..."

        # Try with certificate bundle first, then fallback to insecure if needed
        if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
            print_warning "SSL verification failed, trying with --insecure flag..."
            curl -LsSf --insecure https://astral.sh/uv/install.sh | sh
        fi

        # Add uv to PATH for current session - check multiple possible locations
        if [[ -f "$HOME/.local/bin/uv" ]]; then
            export PATH="$HOME/.local/bin:$PATH"
        elif [[ -f "$HOME/.cargo/bin/uv" ]]; then
            export PATH="$HOME/.cargo/bin:$PATH"
        fi

        # Add to shell rc file
        if [[ "$SHELL" == "/bin/zsh" ]]; then
            if [[ -f "$HOME/.local/bin/uv" ]]; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
            else
                echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc
            fi
        elif [[ "$SHELL" == "/bin/bash" ]]; then
            if [[ -f "$HOME/.local/bin/uv" ]]; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
            else
                echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
            fi
        elif [[ "$SHELL" == "/bin/fish" ]]; then
            if [[ -f "$HOME/.local/bin/uv" ]]; then
                echo 'set -gx PATH $HOME/.local/bin $PATH' >> ~/.config/fish/config.fish
            else
                echo 'set -gx PATH $HOME/.cargo/bin $PATH' >> ~/.config/fish/config.fish
            fi
        fi

        # Verify installation
        if ! command -v uv &> /dev/null; then
            print_error "Failed to install uv. Please install manually with: curl -LsSf https://astral.sh/uv/install.sh | sh"
            exit 1
        fi

        print_success "uv installed successfully"
    else
        print_success "uv is already installed ($(uv --version))"
    fi
}

check_npm() {
    print_step "Ensuring latest Node.js (LTS) and npm are installed..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        print_step "Use nodebrew to install/update latest Node.js LTS"
        if ! command -v nodebrew &> /dev/null; then
            print_step "Install nodebrew"
            if ! command -v brew &> /dev/null; then
                print_error "Homebrew is not installed. Please install Homebrew first."
                exit 1
            fi
            brew install nodebrew
            echo "export PATH=$HOME/.nodebrew/current/bin:$PATH" >> $rc_file
            export PATH="$HOME/.nodebrew/current/bin:$PATH"
        fi
        nodebrew install-binary stable || nodebrew install stable
        nodebrew use stable
        print_success "Node.js $(node -v) installed/updated (latest LTS)"
    elif [[ "$OSTYPE" == "linux"* ]]; then
        print_step "Installing/updating latest Node.js LTS via NodeSource repository..."
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo apt-get install -y nodejs
        print_success "Node.js $(node -v) installed/updated (latest LTS)"
    else
        print_error "Unsupported OS. Please install Node.js 18以上 manually."
        exit 1
    fi

    # Verify installation
    if ! command -v npm &> /dev/null; then
        print_error "Failed to install npm. Please install Node.js manually."
        exit 1
    fi
    print_success "npm is installed ($(npm --version)), Node.js $(node -v)"
}

check_github_cli() {
    if ! command -v gh &> /dev/null; then
        print_step "gh is not installed. Installing GitHub CLI..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            if ! command -v brew &> /dev/null; then
                print_error "Homebrew is not installed. Please install Homebrew first."
                exit 1
            fi
            brew install gh
        elif [[ "$OSTYPE" == "linux"* ]]; then
            type -p curl >/dev/null || sudo apt install curl -y
            if ! curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg; then
                print_warning "SSL verification failed, trying with --insecure flag..."
                curl -fsSL --insecure https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
            fi
            sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
            && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
            && sudo apt update \
            && sudo apt install gh -y
        else
            print_error "Unsupported OS for automatic gh installation."
            exit 1
        fi

        # Verify installation
        if ! command -v gh &> /dev/null; then
            print_error "Failed to install GitHub CLI."
            exit 1
        fi

        print_success "GitHub CLI installed successfully"
        print_step "Please run 'gh auth login' to authenticate with GitHub after setup completes."
    else
        print_success "GitHub CLI is already installed ($(gh --version | head -n1))"
    fi
}

check_claude_code() {
    if ! command -v claude &> /dev/null; then
        print_step "Installing Claude Code..."
        export NODE_ENV=production
        export TERM=xterm-256color
        unset WINDIR
        if sudo npm i -g @anthropic-ai/claude-code; then
            print_success "Claude Code installed"
            print_step "Run 'claude auth' to authenticate after setup completes"
        else
            print_warning "Claude Code installation failed. This might be due to environment detection issues."
            print_step "You can try installing manually later with:"
            echo "  sudo npm i -g @anthropic-ai/claude-code"
            print_step "If the issue persists, check: https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#check-system-requirements"
            exit 1
        fi
    else
        print_success "Claude Code is already installed ($(claude --version))"
    fi
}

check_gemini_cli() {
    if ! command -v gemini &> /dev/null; then
        print_step "Installing Gemini CLI..."
        npm install -g @google/gemini-cli
        print_success "Gemini CLI installed"
        print_step "Run 'gemini auth' to authenticate after setup completes"
    else
        print_success "Gemini CLI is already installed ($(gemini --version))"
    fi
}

check_mermaid_cli() {
    print_step "Installing Mermaid CLI..."
    if ! command -v mmdc &> /dev/null; then
        npm install -g @mermaid-js/mermaid-cli
        print_success "Mermaid CLI installed"
    else
        print_success "Mermaid CLI already installed ($(mmdc --version))"
    fi
}

# Check if make is installed
check_make() {
    if ! command -v make &> /dev/null; then
        print_step "make is not installed. Installing make..."
        if [[ "$OSTYPE" == "linux"* ]]; then
            sudo apt-get update
            sudo apt-get install -y make
            print_success "make installed successfully"
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            if ! command -v brew &> /dev/null; then
                print_error "Homebrew is not installed. Please install Homebrew first."
                exit 1
            fi
            brew install make
            print_success "make installed successfully"
        else
            print_error "Unsupported OS. Please install make manually."
            exit 1
        fi
    else
        print_success "make is already installed ($(make --version | head -n1))"
    fi
}

# Setup Python environment
setup_python() {
    print_step "Setting up Python environment..."

    # Pin Python version
    uv python pin $PYTHON_VERSION
    print_success "Python $PYTHON_VERSION pinned"

    # Install dependencies with dev mode
    print_step "Installing dependencies..."
    uv add --dev --editable .
    print_success "Plugin installed in development mode"

    # Sync additional dependencies
    uv sync --all-extras
    print_success "Dependencies installed"
}

# Setup pre-commit
setup_precommit() {
    print_step "Setting up pre-commit hooks..."

    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg

    # Run pre-commit on all files to ensure everything is set up
    print_step "Running initial pre-commit checks..."
    uv run pre-commit run --all-files || true

    print_success "Pre-commit hooks installed"
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

# 日本語フォントのインストール
install_japanese_fonts() {
    print_step "Installing Japanese fonts..."
    if [[ "$OSTYPE" == "linux"* ]]; then
        sudo apt-get update
        sudo apt-get install -y fonts-noto-cjk fonts-ipafont-gothic fonts-ipafont-mincho fonts-noto-color-emoji
        print_success "Japanese fonts installed (Noto, IPA)"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install --cask font-noto-sans-cjk font-noto-serif-cjk font-ipaexfont
        print_success "Japanese fonts installed (Noto, IPAex)"
    else
        print_warning "Unsupported OS for automatic Japanese font installation. Please install manually."
    fi
}

# Main setup flow
main() {
    echo "🚀 MkDocs Mermaid to Image Plugin Setup"
    echo "======================================="
    echo

    # Check prerequisites
    check_make
    check_uv
    check_npm
    check_claude_code
    check_gemini_cli
    check_mermaid_cli
    check_github_cli

    # 日本語フォントのインストール
    install_japanese_fonts

    # Perform setup
    setup_python
    setup_precommit
    init_git
    test_plugin
    run_tests
    test_mkdocs

    echo
    echo "✨ Setup complete!"
    echo
    echo "Next steps:"
    echo "1. Authenticate with services:"
    echo "   gh auth login         # GitHub CLI authentication"
    echo "   claude auth           # Claude Code authentication"
    echo "   gemini auth           # Gemini CLI authentication"
    echo "2. Initialize project via \`/initialize-project\` via Claude Code"
    echo "3. Set up branch protection (optional):"
    echo "   gh repo view --web  # Open in browser to configure"
    echo "4. Start developing! 🎉"
    echo
    echo "Development commands:"
    echo "  uv run mkdocs serve    # Start development server"
    echo "  uv run mkdocs build    # Build documentation"
    echo "  uv run pytest         # Run tests"
    echo "  uv run pre-commit run --all-files  # Run quality checks"
    echo
    echo "Quality assurance:"
    echo "  make test              # Run tests"
    echo "  make format            # Format code"
    echo "  make lint              # Lint code"
    echo "  make typecheck         # Type check"
    echo "  make check             # Run all checks"
    echo "  make help              # Show all available commands"
    echo
    echo "Plugin development:"
    echo "  uv add <package>       # Add dependency"
    echo "  make pr                # Create pull request"
    echo "  make issue-bug         # Create bug report"
    echo "  make issue-feature     # Create feature request"
    echo "  make issue-claude      # Create Claude Code collaboration issue"
    echo "  make issue             # Create issue (template selection)"
    echo
}

# Run main function
main
