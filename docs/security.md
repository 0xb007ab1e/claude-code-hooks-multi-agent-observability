# Security Documentation

## 🔐 Security Overview

The Multi-Agent Observability System implements multiple security layers to protect sensitive data and prevent unauthorized access. This document outlines security practices, environment variable management, and recommended security measures.

## 🔑 Environment Variables

### Required Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | ✅ | Anthropic Claude API key for agent functionality | `sk-ant-api03-...` |
| `ENGINEER_NAME` | ✅ | User identification for logging and session tracking | `John Doe` |

### Optional Environment Variables

| Variable | Default | Description | Example |
|----------|---------|-------------|---------|
| `OPENAI_API_KEY` | - | OpenAI API key for multi-model support | `sk-proj-...` |
| `ELEVENLABS_API_KEY` | - | ElevenLabs API key for audio features | `sk_...` |
| `ANTHROPIC_MODEL` | `claude-3-5-haiku-20241022` | Default Anthropic model | `claude-3-5-sonnet-20241022` |
| `OPENAI_MODEL` | `gpt-4.1-nano` | Default OpenAI model | `gpt-4` |
| `OPENAI_TTS_MODEL` | `gpt-4o-mini-tts` | OpenAI text-to-speech model | `tts-1` |
| `OPENAI_TTS_VOICE` | `nova` | OpenAI TTS voice selection | `alloy` |
| `ELEVENLABS_MODEL` | `eleven_turbo_v2_5` | ElevenLabs TTS model | `eleven_multilingual_v2` |
| `ELEVENLABS_VOICE_ID` | `WejK3H1m7MI9CHnIjW9K` | ElevenLabs voice ID | `your-voice-id` |
| `CLAUDE_HOOKS_LOG_DIR` | `logs` | Directory for log files | `./logs` |

## 🛠️ Environment Setup

### 1. Create Environment File

Generate your environment configuration from the sample:

```bash
cp .env.sample .env
```

### 2. Configure Required Variables

Edit `.env` file with your actual values:

```bash
# API Keys for AI Services
ANTHROPIC_API_KEY=your_actual_anthropic_key_here
OPENAI_API_KEY=your_actual_openai_key_here
ELEVENLABS_API_KEY=your_actual_elevenlabs_key_here

# User Configuration
ENGINEER_NAME=Your Name

# Model Configuration (optional - defaults provided)
ANTHROPIC_MODEL=claude-3-5-haiku-20241022
OPENAI_MODEL=gpt-4.1-nano
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=nova
ELEVENLABS_MODEL=eleven_turbo_v2_5
ELEVENLABS_VOICE_ID=WejK3H1m7MI9CHnIjW9K

# System Configuration
CLAUDE_HOOKS_LOG_DIR=logs
```

### 3. Verify Configuration

The system will automatically load environment variables when you run:

```bash
./scripts/start_env.sh
```

## 🚨 Secret Management Warnings

### ⚠️ Critical Security Practices

1. **NEVER commit `.env` files to version control**
   - The `.env` file contains sensitive API keys and credentials
   - Always use `.env.sample` as a template without actual values
   - Review commits before pushing to ensure no secrets are included

2. **Use strong, unique API keys**
   - Generate API keys from official provider dashboards
   - Rotate keys regularly (recommended: monthly)
   - Use different keys for development and production environments

3. **Limit API key permissions**
   - Grant minimum required permissions for each API key
   - Monitor API key usage through provider dashboards
   - Revoke unused or compromised keys immediately

## 🔒 Recommended Security Measures

### Pre-commit Hook with git-secrets

Install and configure `git-secrets` to prevent accidental secret commits:

#### Installation

**macOS (Homebrew):**
```bash
brew install git-secrets
```

**Linux (Ubuntu/Debian):**
```bash
# Install from source
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets
sudo make install
```

#### Configuration

1. **Initialize git-secrets for this repository:**
```bash
git secrets --install
git secrets --register-aws
```

2. **Add custom patterns for API keys:**
```bash
# Anthropic API keys
git secrets --add 'sk-ant-api03-[A-Za-z0-9_-]{95}'

# OpenAI API keys
git secrets --add 'sk-proj-[A-Za-z0-9_-]{20,}'
git secrets --add 'sk-[A-Za-z0-9_-]{48,}'

# ElevenLabs API keys
git secrets --add 'sk_[A-Za-z0-9_-]{32,}'

# Generic patterns
git secrets --add '.*API_KEY.*=.*[A-Za-z0-9_-]{20,}'
git secrets --add 'password.*=.*[A-Za-z0-9_-]{8,}'
```

3. **Enable pre-commit hook:**
```bash
git secrets --install ~/.git-templates/git-secrets
git config --global init.templateDir ~/.git-templates/git-secrets
```

4. **Test the configuration:**
```bash
# This should be blocked
echo "ANTHROPIC_API_KEY=sk-ant-api03-test123" > test.txt
git add test.txt
git commit -m "Test commit"  # Should fail
rm test.txt
```

### Additional Security Tools

#### 1. Pre-commit Framework
Install additional security checks:

```bash
pip install pre-commit
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key
      - id: end-of-file-fixer
      - id: trailing-whitespace
  
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
```

#### 2. Environment Validation
The system includes built-in validation for critical environment variables. Missing required variables will result in startup failures with clear error messages.

## 🛡️ Built-in Security Features

### 1. Command Filtering
The system blocks dangerous commands including:
- File system destruction (`rm -rf`, `rmdir`)
- System modifications (`chmod`, `chown`)
- Network operations (`curl`, `wget` to sensitive endpoints)
- Process manipulation (`kill`, `killall`)

### 2. File Access Protection
Protected files and directories:
- Environment files (`.env`, `.env.*`)
- SSH keys (`~/.ssh/`, `*.pem`, `*.key`)
- System configuration files (`/etc/`, `/sys/`)
- Database files (`*.db`, `*.sqlite`)

### 3. Input Validation
All API inputs are validated for:
- Proper JSON formatting
- Required field presence
- Data type validation
- Size limits (max 1MB per request)

### 4. Rate Limiting
- WebSocket connections: 100 connections per IP
- HTTP API: 1000 requests per minute per IP
- Event processing: 10,000 events per session

## 🔐 Responsible Disclosure

### Security Vulnerabilities

If you discover a security vulnerability in this system, please report it responsibly:

1. **Email:** security@example.com (Replace with actual security contact)
2. **Encrypted communication:** Use PGP key available at security.example.com/pgp
3. **Timeline:** We aim to respond within 24 hours and provide updates every 72 hours

### What to Include

- **Detailed description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** assessment
- **Suggested remediation** if available
- **Your contact information** for follow-up

### What We Promise

- **Acknowledgment** within 24 hours
- **Regular updates** on investigation progress
- **Credit** in security advisories (if desired)
- **No legal action** for good-faith security research

## 📋 Security Checklist

Before deploying or sharing this system:

- [ ] All API keys configured in `.env` file
- [ ] `.env` file added to `.gitignore`
- [ ] `git-secrets` installed and configured
- [ ] Pre-commit hooks enabled
- [ ] Environment variables validated
- [ ] Log directory permissions set correctly
- [ ] No hardcoded secrets in source code
- [ ] Database files excluded from version control
- [ ] Network access limited to required services
- [ ] Regular security updates scheduled

## 🔄 Security Maintenance

### Monthly Tasks
- [ ] Rotate API keys
- [ ] Review access logs
- [ ] Update dependencies
- [ ] Check for new security advisories

### Quarterly Tasks
- [ ] Security audit of hook scripts
- [ ] Review git-secrets patterns
- [ ] Update security documentation
- [ ] Test backup and recovery procedures

### Annual Tasks
- [ ] Complete security assessment
- [ ] Update incident response plan
- [ ] Review and update security policies
- [ ] Penetration testing (if applicable)

## 📖 Additional Resources

- [Anthropic API Security Best Practices](https://docs.anthropic.com/claude/docs/security)
- [OpenAI API Security Guidelines](https://platform.openai.com/docs/guides/safety-best-practices)
- [Git Secrets Documentation](https://github.com/awslabs/git-secrets)
- [Pre-commit Framework](https://pre-commit.com/)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)

---

**Last Updated:** 2025-07-14  
**Version:** 1.0  
**Status:** Active
