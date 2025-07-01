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
    print_step "Installing/updating latest Node.js LTS via NodeSource repository..."
    if ! curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -; then
        print_warning "SSL verification failed, trying with --insecure flag..."
        curl -fsSL --insecure https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    fi
    sudo apt-get install -y nodejs
    print_success "Node.js $(node -v) installed/updated (latest LTS)"

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
        type -p curl >/dev/null || sudo apt install curl -y
        if ! curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg; then
            print_warning "SSL verification failed, trying with --insecure flag..."
            curl -fsSL --insecure https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        fi
        sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
        && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
        && sudo apt update \
        && sudo apt install gh -y

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

check_make() {
    if ! command -v make &> /dev/null; then
        print_step "make is not installed. Installing make..."
        sudo apt-get update
        sudo apt-get install -y make
        print_success "make installed successfully"
    else
        print_success "make is already installed ($(make --version | head -n1))"
    fi
}

install_update_uv() {
    print_step "Installing/updating uv to latest version..."

    # Always install/update to latest version
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

    print_success "uv installed/updated successfully ($(uv --version))"
}

install_update_npm() {
    print_step "Installing/updating Node.js (LTS) and npm to latest versions..."
    print_step "Installing/updating latest Node.js LTS via NodeSource repository..."
    if ! curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -; then
        print_warning "SSL verification failed, trying with --insecure flag..."
        curl -fsSL --insecure https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    fi
    sudo apt-get install -y nodejs
    print_success "Node.js $(node -v) installed/updated (latest LTS)"

    # Verify installation
    if ! command -v npm &> /dev/null; then
        print_error "Failed to install npm. Please install Node.js manually."
        exit 1
    fi
    print_success "npm installed/updated ($(npm --version)), Node.js $(node -v)"
}

install_update_github_cli() {
    print_step "Installing/updating GitHub CLI to latest version..."
    type -p curl >/dev/null || sudo apt-get install curl -y
    if ! curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg; then
        print_warning "SSL verification failed, trying with --insecure flag..."
        curl -fsSL --insecure https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    fi
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && sudo apt-get update \
    && sudo apt-get install gh -y

    # Verify installation
    if ! command -v gh &> /dev/null; then
        print_error "Failed to install GitHub CLI."
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

install_update_mermaid_cli() {
    print_step "Installing/updating Mermaid CLI to latest version..."
    # Always install/update to latest
    npm install -g @mermaid-js/mermaid-cli@latest
    print_success "Mermaid CLI installed/updated ($(mmdc --version))"
}

install_update_make() {
    print_step "Installing/updating make..."
    sudo apt-get install -y make
    print_success "make installed/updated successfully"
    print_success "make is available ($(make --version | head -n1))"
}

update_system_packages() {
    print_step "Updating system packages..."
    sudo apt-get update
    print_success "System packages updated"
}

install_update_cargo() {
    print_step "Installing/updating Rust and Cargo to latest version..."

    # Try apt first on Linux for better SSL compatibility
    print_step "Installing Rust and Cargo via apt package manager..."
    if sudo apt-get install -y cargo rustc; then
        print_success "Rust/Cargo installed via apt package manager"
    else
        print_warning "apt installation failed, trying rustup installer..."
        # Fallback to rustup installer with SSL fallback
        if ! curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; then
            print_warning "SSL verification failed, trying with --insecure flag..."
            curl --proto '=https' --tlsv1.2 -sSf --insecure https://sh.rustup.rs | sh -s -- -y
        fi

        # Source cargo environment for rustup installation
        source "$HOME/.cargo/env" 2>/dev/null || true
        export PATH="$HOME/.cargo/bin:$PATH"

        # Add to shell rc file for rustup installation
        if [[ "$SHELL" == "/bin/zsh" ]]; then
            echo 'source "$HOME/.cargo/env"' >> ~/.zshrc
        elif [[ "$SHELL" == "/bin/bash" ]]; then
            echo 'source "$HOME/.cargo/env"' >> ~/.bashrc
        elif [[ "$SHELL" == "/bin/fish" ]]; then
            echo 'set -gx PATH $HOME/.cargo/bin $PATH' >> ~/.config/fish/config.fish
        fi
    fi

    # Update to latest stable if rustup is available (for rustup installations)
    if command -v rustup &> /dev/null; then
        rustup update stable
        rustup default stable
    fi

    # Verify installation
    if ! command -v cargo &> /dev/null; then
        print_error "Failed to install Rust/Cargo. Please install manually."
        exit 1
    fi

    print_success "Rust/Cargo installed/updated successfully ($(cargo --version))"
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

    # Update system packages once at the beginning
    update_system_packages

    # Install/update all tools to latest versions
    install_update_make
    install_update_cargo
    install_update_uv
    install_update_npm
    install_update_mermaid_cli
    install_update_github_cli
    install_update_claude_code
    install_update_gemini_cli

    # Install/update Japanese fonts
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
