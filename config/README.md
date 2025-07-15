# Environment Configuration

This directory contains environment configuration files for the Multi-Agent Observability System.

## Files

### `.env`
Contains environment variables for the application, including:
- `CLAUDE_API_KEY`: Your Claude/Anthropic API key
- `CLAUDE_API_URL`: The Claude API endpoint URL
- Additional service keys and configuration

**Important**: This file is git-ignored and should never be committed to version control.

## Setup

1. Copy the environment file and update with your actual keys:
   ```bash
   # Edit the .env file with your actual API keys
   nano config/.env
   ```

2. Set up your workspace by running the initialization script:
   ```bash
   ./scripts/workspace-init.sh
   ```

   Or manually source the environment file:
   ```bash
   source config/.env
   ```

## Usage

The environment variables are automatically loaded when you:
- Run `./scripts/workspace-init.sh` for manual workspace setup
- Run `./scripts/start-system.sh` (automatically sources the env file)

## Security Notes

- Never commit the `.env` file to version control
- Keep your API keys secure and rotate them regularly
- The `.env` file is already included in `.gitignore`
