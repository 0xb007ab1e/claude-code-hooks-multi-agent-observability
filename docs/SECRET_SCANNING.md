# Secret Scanning

This project uses automated secret scanning to prevent sensitive information from being committed to the repository.

## Overview

Our CI/CD pipeline includes automated secret scanning using:

- **TruffleHog**: Advanced secret detection with verification capabilities
- **GitLeaks**: Comprehensive pattern-based secret detection

Both tools run automatically on:
- Every push to `main` and `develop` branches
- Every pull request to `main` and `develop` branches

## What Gets Scanned

The secret scanners look for:
- API keys and tokens
- Database credentials
- Private keys and certificates
- AWS/cloud provider credentials
- OAuth tokens
- Generic high-entropy strings that might be secrets

## If the Scan Fails

When the secret scan fails, it means potential secrets were detected. Follow these steps:

1. **Check the GitHub Actions logs** to see what was detected
2. **Determine if it's a real secret or false positive**
3. **If it's a real secret**: Remove it immediately and rotate the credential
4. **If it's a false positive**: Follow the suppression guide in [`docs/SECRET_SCAN_SUPPRESSION.md`](SECRET_SCAN_SUPPRESSION.md)

## Configuration Files

- **`.gitleaks.toml`**: GitLeaks configuration and allowlist rules
- **`.trufflehog-exclude`**: TruffleHog exclusion patterns (one regex per line)
- **`.github/workflows/secret-scan.yml`**: GitHub Actions workflow

## Running Scans Locally

Test the secret scanners locally before pushing:

```bash
# Run GitLeaks
docker run --rm -v $(pwd):/code ghcr.io/gitleaks/gitleaks:latest detect --source=/code --config=/code/.gitleaks.toml

# Run TruffleHog
docker run --rm -v $(pwd):/code trufflesecurity/trufflehog:latest filesystem --exclude-paths=/code/.trufflehog-exclude --results=verified --fail /code
```

## Best Practices

### ✅ Do:
- Use environment variables for all secrets
- Store sensitive configuration in `.env` files (not committed)
- Use placeholder values in documentation and examples
- Test your code with the secret scanners before committing

### ❌ Don't:
- Commit real API keys, passwords, or tokens
- Use inline suppression comments unless absolutely necessary
- Suppress broad patterns that might miss real secrets
- Ignore secret scan failures

## Getting Help

If you need help with secret scanning:

1. Read the [suppression guide](SECRET_SCAN_SUPPRESSION.md)
2. Check existing issues for similar problems
3. Create a new issue with the scanner output and your analysis
4. Contact the security team for guidance

## Security Contact

For security-related issues or questions about secret scanning, please contact the security team or create a security issue in the repository.
