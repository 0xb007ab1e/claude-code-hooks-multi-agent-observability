# =============================================================================
# CROSS-PLATFORM ENVIRONMENT VARIABLE LOADER (PowerShell)
# =============================================================================
# This script loads environment variables from the centralized .env file
# and exports them for use by any stack/application in the repository.
#
# Usage:
#   . config/env-helpers/load-env.ps1
#   . config/env-helpers/load-env.ps1 -EnvFile "path/to/custom/.env"
#
# Author: Centralized Configuration Management System
# =============================================================================

param(
    [string]$EnvFile = ""
)

# Color constants for output
$Colors = @{
    Red = "Red"
    Green = "Green"
    Yellow = "Yellow"
    Blue = "Blue"
    White = "White"
}

# Function to print colored output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Colors.Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Colors.Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Red
}

# Function to validate required variables
function Test-RequiredVariables {
    $RequiredVars = @(
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "ELEVENLABS_API_KEY",
        "PORT",
        "NODE_ENV"
    )
    
    $MissingVars = @()
    
    foreach ($var in $RequiredVars) {
        if (-not (Test-Path "env:$var") -or [string]::IsNullOrEmpty((Get-Item "env:$var").Value)) {
            $MissingVars += $var
        }
    }
    
    if ($MissingVars.Count -gt 0) {
        Write-Error "Missing required environment variables:"
        foreach ($var in $MissingVars) {
            Write-Host "  - $var"
        }
        return $false
    }
    
    return $true
}

# Function to set default values
function Set-DefaultValues {
    # Set default values for optional variables
    if (-not $env:ANTHROPIC_MODEL) { $env:ANTHROPIC_MODEL = "claude-3-5-haiku-20241022" }
    if (-not $env:OPENAI_MODEL) { $env:OPENAI_MODEL = "gpt-4.1-nano" }
    if (-not $env:OPENAI_TTS_MODEL) { $env:OPENAI_TTS_MODEL = "gpt-4o-mini-tts" }
    if (-not $env:OPENAI_TTS_VOICE) { $env:OPENAI_TTS_VOICE = "nova" }
    if (-not $env:ELEVENLABS_MODEL) { $env:ELEVENLABS_MODEL = "eleven_turbo_v2_5" }
    if (-not $env:ELEVENLABS_VOICE_ID) { $env:ELEVENLABS_VOICE_ID = "WejK3H1m7MI9CHnIjW9K" }
    if (-not $env:ENGINEER_NAME) { $env:ENGINEER_NAME = "Dan" }
    if (-not $env:DATABASE_PATH) { $env:DATABASE_PATH = "events.db" }
    if (-not $env:CORS_ORIGINS) { $env:CORS_ORIGINS = "*" }
    if (-not $env:RATE_LIMIT_WINDOW_MS) { $env:RATE_LIMIT_WINDOW_MS = "900000" }
    if (-not $env:RATE_LIMIT_MAX_REQUESTS) { $env:RATE_LIMIT_MAX_REQUESTS = "100" }
    if (-not $env:WS_HEARTBEAT_INTERVAL) { $env:WS_HEARTBEAT_INTERVAL = "30000" }
    if (-not $env:LOG_LEVEL) { $env:LOG_LEVEL = "info" }
    if (-not $env:CLAUDE_HOOKS_LOG_DIR) { $env:CLAUDE_HOOKS_LOG_DIR = "logs" }
    if (-not $env:VITE_MAX_EVENTS_TO_DISPLAY) { $env:VITE_MAX_EVENTS_TO_DISPLAY = "100" }
    if (-not $env:VITE_WEBSOCKET_URL) { $env:VITE_WEBSOCKET_URL = "ws://localhost:4000/stream" }
    if (-not $env:DB_HOST) { $env:DB_HOST = "localhost" }
    if (-not $env:DB_PORT) { $env:DB_PORT = "5432" }
    if (-not $env:DB_NAME) { $env:DB_NAME = "observability" }
    if (-not $env:COMPOSE_PROJECT_NAME) { $env:COMPOSE_PROJECT_NAME = "observability" }
    if (-not $env:DOCKER_NETWORK_NAME) { $env:DOCKER_NETWORK_NAME = "observability-network" }
    if (-not $env:DEV_MODE) { $env:DEV_MODE = "true" }
    if (-not $env:DEBUG_MODE) { $env:DEBUG_MODE = "false" }
    if (-not $env:VERBOSE_LOGGING) { $env:VERBOSE_LOGGING = "false" }
    if (-not $env:HOT_RELOAD) { $env:HOT_RELOAD = "true" }
    if (-not $env:WATCH_FILES) { $env:WATCH_FILES = "true" }
    
    # Stack-specific port defaults
    if (-not $env:GO_PORT) { $env:GO_PORT = "4001" }
    if (-not $env:PYTHON_PORT) { $env:PYTHON_PORT = "4002" }
    if (-not $env:RUST_PORT) { $env:RUST_PORT = "4003" }
    if (-not $env:DOTNET_PORT) { $env:DOTNET_PORT = "4004" }
}

# Function to load environment variables from .env file
function Import-EnvFile {
    param([string]$FilePath)
    
    if (-not (Test-Path $FilePath)) {
        Write-Error "Environment file not found: $FilePath"
        return $false
    }
    
    Write-Info "Loading environment variables from: $FilePath"
    
    try {
        $content = Get-Content $FilePath -ErrorAction Stop
        
        foreach ($line in $content) {
            # Skip empty lines and comments
            if ([string]::IsNullOrWhiteSpace($line) -or $line.TrimStart().StartsWith("#")) {
                continue
            }
            
            # Parse key=value pairs
            if ($line -match "^([^=]+)=(.*)$") {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                
                # Remove quotes if present
                $value = $value -replace '^"(.*)"$', '$1'
                $value = $value -replace "^'(.*)'$", '$1'
                
                # Set environment variable
                [Environment]::SetEnvironmentVariable($key, $value, [EnvironmentVariableTarget]::Process)
            }
        }
        
        return $true
    }
    catch {
        Write-Error "Failed to read environment file: $($_.Exception.Message)"
        return $false
    }
}

# Function to print loaded environment summary
function Show-EnvironmentSummary {
    Write-Info "Environment Summary:"
    Write-Host "  NODE_ENV: $env:NODE_ENV"
    Write-Host "  PORT: $env:PORT"
    Write-Host "  DATABASE_PATH: $env:DATABASE_PATH"
    Write-Host "  LOG_LEVEL: $env:LOG_LEVEL"
    Write-Host "  CORS_ORIGINS: $env:CORS_ORIGINS"
    
    # Check if API keys are set (without exposing them)
    if (-not [string]::IsNullOrEmpty($env:ANTHROPIC_API_KEY)) {
        Write-Host "  ANTHROPIC_API_KEY: ✓ Set"
    } else {
        Write-Host "  ANTHROPIC_API_KEY: ✗ Not set"
    }
    
    if (-not [string]::IsNullOrEmpty($env:OPENAI_API_KEY)) {
        Write-Host "  OPENAI_API_KEY: ✓ Set"
    } else {
        Write-Host "  OPENAI_API_KEY: ✗ Not set"
    }
    
    if (-not [string]::IsNullOrEmpty($env:ELEVENLABS_API_KEY)) {
        Write-Host "  ELEVENLABS_API_KEY: ✓ Set"
    } else {
        Write-Host "  ELEVENLABS_API_KEY: ✗ Not set"
    }
}

# Main function
function Main {
    # Determine the root directory (where this script is located)
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Resolve-Path (Join-Path $ScriptDir "../..")
    
    # Determine .env file path
    if ([string]::IsNullOrEmpty($EnvFile)) {
        $EnvFile = Join-Path $RepoRoot ".env"
    }
    
    # If .env doesn't exist, try .env.example
    if (-not (Test-Path $EnvFile)) {
        $ExampleFile = Join-Path $RepoRoot ".env.example"
        if (Test-Path $ExampleFile) {
            Write-Warning ".env file not found, using .env.example"
            Write-Warning "Please copy .env.example to .env and configure your values"
            $EnvFile = $ExampleFile
        } else {
            Write-Error "No .env or .env.example file found in: $RepoRoot"
            return
        }
    }
    
    # Load environment variables
    if (Import-EnvFile $EnvFile) {
        Set-DefaultValues
        
        # Validate required variables
        if (Test-RequiredVariables) {
            Write-Success "Environment variables loaded successfully"
            Show-EnvironmentSummary
        } else {
            Write-Error "Environment validation failed"
            return
        }
    } else {
        Write-Error "Failed to load environment file"
        return
    }
}

# Run main function
Main
