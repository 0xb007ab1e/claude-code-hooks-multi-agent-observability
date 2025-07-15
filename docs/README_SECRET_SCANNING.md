## 🔒 Secret Scanning

This project includes automated secret scanning to prevent sensitive information from being committed to the repository. The CI/CD pipeline uses TruffleHog and GitLeaks to scan for:

- API keys and tokens
- Database credentials  
- Private keys and certificates
- AWS/cloud provider credentials
- OAuth tokens
- Generic high-entropy strings that might be secrets

### When Secret Scans Fail

If a secret scan fails in CI:

1. **Check the GitHub Actions logs** to see what was detected
2. **Determine if it's a real secret or false positive**
3. **If it's a real secret**: Remove it immediately and rotate the credential
4. **If it's a false positive**: Follow the [suppression guide](docs/SECRET_SCAN_SUPPRESSION.md)

### Documentation

- [Secret Scanning Overview](docs/SECRET_SCANNING.md)
- [False Positive Suppression Guide](docs/SECRET_SCAN_SUPPRESSION.md)

### Running Scans Locally

```bash
# Run GitLeaks
docker run --rm -v $(pwd):/code ghcr.io/gitleaks/gitleaks:latest detect --source=/code --config=/code/.gitleaks.toml

# Run TruffleHog
docker run --rm -v $(pwd):/code trufflesecurity/trufflehog:latest filesystem --exclude-paths=/code/.trufflehog-exclude --results=verified --fail /code
```

### Configuration Files

- `.gitleaks.toml`: GitLeaks configuration and allowlist rules
- `.trufflehog-exclude`: TruffleHog exclusion patterns
- `.github/workflows/secret-scan.yml`: GitHub Actions workflow
