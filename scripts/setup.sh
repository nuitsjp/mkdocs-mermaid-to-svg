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

# Install/update functions - unified package management

install_update_make() {
    print_step "Installing/updating build tools..."
    sudo apt-get install -y build-essential make
    print_success "Build tools installed/updated successfully"
    print_success "make is available ($(make --version | head -n1))"
}

install_update_uv() {
    print_step "Installing/updating uv to latest version..."

    # Install pipx if not available
    if ! command -v pipx &> /dev/null; then
        print_step "Installing pipx..."
        sudo apt-get update
        sudo apt-get install -y pipx
        # Ensure pipx is in PATH
        pipx ensurepath
    fi

    # Install or upgrade uv using pipx
    if command -v uv &> /dev/null; then
        print_step "Upgrading uv via pipx..."
        pipx upgrade uv
    else
        print_step "Installing uv via pipx..."
        pipx install uv
    fi

    # Ensure uv is in PATH
    export PATH="$HOME/.local/bin:$PATH"

    # Verify installation
    if ! command -v uv &> /dev/null; then
        print_error "Failed to install uv via pipx. Please install pipx manually."
        exit 1
    fi

    print_success "uv installed/updated successfully ($(uv --version))"
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

install_update_claude_code() {
    print_step "Installing/updating Claude Code to latest version..."
    export NODE_ENV=production
    export TERM=xterm-256color
    unset WINDIR
    # Always install/update to latest
    if sudo npm i -g @anthropic-ai/claude-code@latest; then
        print_success "Claude Code installed/updated ($(claude --version))"
        if ! claude auth status &> /dev/null; then
            print_step "Run 'claude auth' to authenticate after setup completes"
        fi
    else
        print_warning "Claude Code installation failed. This might be due to environment detection issues."
        print_step "You can try installing manually later with:"
        echo "  sudo npm i -g @anthropic-ai/claude-code@latest"
        print_step "If the issue persists, check: https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview#check-system-requirements"
        exit 1
    fi
}

install_update_gemini_cli() {
    print_step "Installing/updating Gemini CLI to latest version..."
    # Always install/update to latest
    npm install -g @google/gemini-cli@latest
    print_success "Gemini CLI installed/updated ($(gemini --version))"
    print_step "Run 'gemini auth' to authenticate after setup completes"
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

setup_mermaid_local() {
    print_step "Setting up Mermaid CLI locally..."

    # Install Mermaid CLI locally via npm (not globally)
    print_step "Installing Mermaid CLI locally..."
    npm install

    # Install Chrome headless shell for Puppeteer
    print_step "Installing Chrome headless shell for Puppeteer..."
    npx puppeteer browsers install chrome-headless-shell

    # Verify local installation
    if npx mmdc --version > /dev/null 2>&1; then
        print_success "Mermaid CLI installed locally ($(npx mmdc --version))"
    else
        print_error "Failed to install Mermaid CLI locally"
        exit 1
    fi
}

update_system_packages() {
    print_step "Updating system packages..."
    sudo apt-get update
    print_success "System packages updated"
}

install_update_cargo() {
    print_step "Installing/updating Rust and Cargo to latest version..."

    # Install Rust and Cargo via apt package manager
    print_step "Installing Rust and Cargo via apt package manager..."
    sudo apt-get install -y cargo rustc build-essential

    # Verify installation
    if ! command -v cargo &> /dev/null; then
        print_error "Failed to install Rust/Cargo via apt. Please install manually."
        exit 1
    fi

    print_success "Rust/Cargo installed/updated successfully ($(cargo --version))"
}

install_update_similarity_py() {
    print_step "Installing/updating similarity-py to latest version..."

    # Ensure cargo bin path is in PATH
    export PATH="$HOME/.cargo/bin:$PATH"

    # Install similarity-py via cargo with SSL fallback
    if ! cargo install similarity-py; then
        print_warning "SSL verification failed, trying with insecure registry..."
        # Create cargo config for insecure registry access
        mkdir -p "$HOME/.cargo"
        cat > "$HOME/.cargo/config.toml" << EOF
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "vendor"

[http]
check-revoke = false

[net]
git-fetch-with-cli = true
EOF

        # Try with git-based installation as fallback
        print_step "Trying alternative installation method..."
        if ! cargo install --git https://github.com/mizchi/similarity similarity-py; then
            print_error "Failed to install similarity-py. Skipping this tool."
            print_warning "You can try installing manually later with:"
            echo "  cargo install similarity-py"
            echo "  or check: https://github.com/mizchi/similarity"
            return 0  # Don't exit, just skip this tool
        fi
    fi

    # Ensure cargo bin path is permanently added to PATH
    if ! grep -q 'export PATH="$HOME/.cargo/bin:$PATH"' ~/.bashrc; then
        print_step "Adding cargo bin directory to PATH in ~/.bashrc..."
        echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    fi

    # Verify installation with explicit path
    if [ -f "$HOME/.cargo/bin/similarity-py" ]; then
        print_success "similarity-py installed/updated successfully (binary found at $HOME/.cargo/bin/similarity-py)"
        print_step "Note: You may need to run 'source ~/.bashrc' or restart your terminal to use 'similarity-py' command"
    else
        print_warning "similarity-py binary not found at expected location, but continuing setup..."
        return 0
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

install_japanese_fonts() {
    print_step "Installing/updating Japanese fonts..."
    sudo apt-get install -y fonts-noto-cjk fonts-ipafont-gothic fonts-ipafont-mincho fonts-noto-color-emoji
    print_success "Japanese fonts installed/updated (Noto, IPA)"
}

# Main setup flow
main() {
    echo "🚀 MkDocs Mermaid to Image Plugin Setup"
    echo "======================================="
    echo

    # === SYSTEM PREPARATION ===
    # Update package repositories once at the beginning
    update_system_packages

    # === PACKAGE INSTALLATION (by package manager) ===

    # APT packages: System tools and development dependencies
    install_update_make          # build-essential, make (development tools)
    install_update_cargo         # cargo, rustc (Rust toolchain)
    install_update_github_cli    # gh (GitHub CLI)
    install_japanese_fonts       # fonts-noto-cjk, fonts-ipafont-* (CJK font support)
    install_puppeteer_dependencies # Puppeteer Chrome browser dependencies

    # SNAP packages: Modern tools with latest versions
    install_update_npm           # Node.js LTS + npm (JavaScript runtime)

    # PIPX packages: Python ecosystem tools
    install_update_uv            # uv (modern Python package manager)

    # CARGO packages: Rust ecosystem tools
    install_update_similarity_py # similarity-py (Python code similarity detection)

    # NPM global packages: Node.js ecosystem tools (except Mermaid CLI)
    install_update_claude_code   # @anthropic-ai/claude-code (AI assistant)
    install_update_gemini_cli    # @google/gemini-cli (Google AI)

    # === PROJECT SETUP ===

    # Mermaid CLI local setup (project-specific)
    setup_mermaid_local         # npm: local Mermaid CLI + Puppeteer browsers

    # Python environment and dependencies
    setup_python                 # uv: Python version pin, install dependencies
    setup_precommit             # uv: pre-commit hooks installation

    # Version control initialization
    init_git                    # git: repository initialization if needed

    # === VERIFICATION ===

    # Plugin functionality tests
    test_plugin                 # uv: import test, entry point verification
    run_tests                   # uv: pytest execution
    test_mkdocs                 # uv: MkDocs build test

    # === COMPLETION ===
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
