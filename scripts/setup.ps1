#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Sets up the development environment for the MkDocs Mermaid to Image plugin on Windows using winget.
.DESCRIPTION
    This script performs the following actions:
    - Installs necessary system dependencies using winget (Git, Python, Node.js).
    - Installs GitHub CLI.
    - Creates a Python virtual environment.
    - Installs Python and Node.js dependencies using uv and npm.
    - Sets up pre-commit hooks.
    - Runs verification steps (tests and build).
.NOTES
    Author: Gemini
    Requires: Windows PowerShell or PowerShell Core, running as Administrator.
              winget package manager (included in modern Windows versions).
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Helper Functions (using approved verbs) ---

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $($Message)" -ForegroundColor Green
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "Error: $($Message)" -ForegroundColor Red
    exit 1
}

function Write-WarningMessage {
    param([string]$Message)
    Write-Host "Warning: $($Message)" -ForegroundColor Yellow
}

function Write-SuccessMessage {
    param([string]$Message)
    Write-Host "✓ $($Message)" -ForegroundColor Green
}

function Test-CommandExists {
    param([string]$CommandName)
    return (Get-Command $CommandName -ErrorAction SilentlyContinue)
}

function Add-GnuWin32ToPath {
    Write-Step "Checking Make command availability..."

    # First, check if make command is already available
    if (Test-CommandExists "make") {
        Write-SuccessMessage "Make command is already available"
        return $true
    }

    Write-Step "Make command not found. Checking GnuWin32 PATH configuration..."

    $gnuWin32Path = "C:\Program Files (x86)\GnuWin32\bin"

    # Check if make.exe exists in GnuWin32 directory
    $makeExePath = Join-Path $gnuWin32Path "make.exe"
    if (-not (Test-Path $makeExePath)) {
        Write-WarningMessage "make.exe not found in $gnuWin32Path"
        return $false
    }

    # Add to system PATH only if make command is not available
    Write-Step "Adding GnuWin32 to system PATH..."
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")

    # Add to system PATH
    $newPath = $currentPath + ";" + $gnuWin32Path
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "Machine")

    # Update current session PATH
    $env:PATH = $env:PATH + ";" + $gnuWin32Path
}

function Install-WingetPackage {
    param([string]$PackageId)
    Write-Step "Installing winget package: $PackageId..."
    # Using --source winget to ensure we use the main repository
    winget install --id $PackageId -e --source winget --accept-source-agreements --accept-package-agreements
    Write-SuccessMessage "$PackageId has been installed."
}

# --- Main Setup Flow ---

function main {
    Write-Host "🚀 MkDocs Mermaid to Image Plugin Setup (Windows with winget)"
    Write-Host "============================================================"

    Set-Location "$PSScriptRoot\.."

    Install-WingetPackage -PackageId "GitHub.cli"
    Install-WingetPackage -PackageId "GnuWin32.Make"

    # Configure PATH for GnuWin32 Make
    Add-GnuWin32ToPath

    Install-WingetPackage -PackageId "Python.Python.3.12"
    Install-WingetPackage -PackageId "OpenJS.NodeJS.LTS"

    # === PYTHON SETUP ===
    Write-Step "Creating Python virtual environment..."
    python3 -m venv .venv

    Write-Step "Installing uv in virtual environment..."
    pip install uv                              # uvの導入
    uv add --dev --editable .                   # プロジェクトを開発モード（editable）でインストールし、開発用依存（dev）も追加
    uv sync --all-extras                        # pyproject.toml で定義された全ての追加依存の導入
    uv run pre-commit install
    uv run pre-commit install --hook-type commit-msg

    Write-Step "Installing global npm packages..."
    npm install -g @mermaid-js/mermaid-cli

    # Plugin functionality tests
    make test             # uv: pytest execution
    make build             # uv: MkDocs build test

    # === COMPLETION ===
    Write-Host ""
    Write-Host "✨ Setup complete!" -ForegroundColor Cyan
    Write-Host ""
}

# Run main function
main
