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
        print_error "uv is not installed."
        echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
}

check_npm() {
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed."
        # if macos, use nodebrew
        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_step "Use nodebrew to install Node.js"
            if ! command -v nodebrew &> /dev/null; then
                print_step "Install nodebrew"
                brew install nodebrew
                echo "export PATH=$HOME/.nodebrew/current/bin:$PATH" >> $rc_file
                source $rc_file
            fi
            nodebrew install stable
            nodebrew use stable
            print_success "Node.js installed"
        elif [[ "$OSTYPE" == "linux"* ]]; then
            print_step "Use n to install Node.js"
            if ! command -v n &> /dev/null; then
                print_step "Install n"
                sudo apt update
                sudo apt install -y nodejs npm
                sudo npm install n -g
                n stable
                sudo apt purge -y nodejs npm
                sudo apt autoremove -y
            fi
            n stable
            print_success "Node.js installed"
        else
            print_error "Unsupported OS. Please install Node.js manually."
        fi
        exit 1
    fi
}

check_github_cli() {
    if ! command -v gh &> /dev/null; then
        print_error "gh is not installed."
        print_step "Install gh"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install gh
            gh auth login
        elif [[ "$OSTYPE" == "linux"* ]]; then
            type -p curl >/dev/null || sudo apt install curl -y
            curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
            && sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
            && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
            && sudo apt update \
            && sudo apt install gh -y \
            && gh auth login
        fi
        print_success "gh installed"
    fi
}

check_claude_code() {
    print_step "Installing Claude Code..."
    npm i -g @anthropic-ai/claude-code
    print_success "Claude Code installed"
    print_step "Checking Claude Code..."
    claude --version
    print_success "Claude Code checked"
}

check_gemini_cli() {
    print_step "Installing Gemini CLI..."
    npm install -g @google/gemini-cli
    print_success "Gemini CLI installed"
    print_step "Checking Gemini CLI..."
    gemini --version
    print_success "Gemini CLI checked"
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

# Main setup flow
main() {
    echo "🚀 MkDocs Mermaid to Image Plugin Setup"
    echo "======================================="
    echo

    # Check prerequisites
    check_uv
    check_npm
    check_claude_code
    check_gemini_cli
    check_mermaid_cli
    check_github_cli

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
    echo "1. Authorize Claude Code and Gemini CLI"
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
