# Secret Scan Suppression Guide

This document explains how to handle false positives in our automated secret scanning system that uses TruffleHog and GitLeaks.

## Overview

Our CI/CD pipeline automatically scans for secrets using two tools:
- **TruffleHog**: Focuses on verified secrets with lower false positive rates
- **GitLeaks**: Comprehensive pattern-based secret detection

When the secret scan fails, it means potential secrets were detected. This guide helps you determine if these are legitimate security concerns or false positives that need to be suppressed.

## Step 1: Analyze the Scan Results

1. **Check the GitHub Actions logs** in the failed workflow
2. **Review the detected patterns** - look for:
   - File names and line numbers
   - The specific text that triggered the detection
   - The type of secret detector that fired

3. **Determine if it's a real secret**:
   - ✅ **Real Secret**: Actual API keys, passwords, tokens, or credentials
   - ❌ **False Positive**: Test data, documentation examples, placeholder values, or non-sensitive strings

## Step 2: Handle Real Secrets

If you've identified a real secret:

1. **Remove the secret immediately** from the codebase
2. **Invalidate/rotate the secret** in the external service
3. **Use environment variables** or secure secret management instead
4. **Consider using git history rewriting** if the secret was recently committed

```bash
# Remove secret from latest commit
git reset HEAD~1
# Edit files to remove secret
git add .
git commit -m "Remove secret from codebase"

# For older commits, consider using git filter-branch or BFG Repo-Cleaner
```

## Step 3: Suppress False Positives

### Option A: Update GitLeaks Configuration

Edit `.gitleaks.toml` to add suppression rules:

#### 1. File-based suppression
```toml
[allowlist]
files = [
    '''path/to/your/file\.ext$''',
    '''test/fixtures/.*''',
]
```

#### 2. Regex-based suppression
```toml
[allowlist]
regexes = [
    '''your-specific-pattern-here''',
    '''(?i)(dummy|example|test)_secret_value''',
]
```

#### 3. Commit-based suppression (use sparingly)
```toml
[allowlist]
commits = [
    "commit-hash-here",
]
```

### Option B: Update TruffleHog Configuration

Edit `.trufflehog-exclude` to add exclusions (one regex pattern per line):

#### 1. File pattern exclusions
```
# Add specific file patterns
path/to/specific/file\.ext$
test/fixtures/.*
docs/.*
.*\.example$
```

#### 2. Directory exclusions
```
# Add directory patterns
temp/.*
backup/.*
```

### Option C: Inline Suppression Comments

For GitLeaks, you can add inline comments to suppress specific lines:

```javascript
const apiKey = "sk-1234567890abcdef"; // gitleaks:allow
```

```python
SECRET_KEY = "dummy-secret-for-testing"  # gitleaks:allow
```

## Step 4: Test Your Changes

After adding suppression rules:

1. **Run the secret scan locally** to verify the suppression works:

```bash
# Test GitLeaks locally
docker run --rm -v $(pwd):/code ghcr.io/gitleaks/gitleaks:latest detect --source=/code --config=/code/.gitleaks.toml

# Test TruffleHog locally
docker run --rm -v $(pwd):/code trufflesecurity/trufflehog:latest filesystem --exclude-paths=/code/.trufflehog-exclude --results=verified --fail /code
```

2. **Commit and push your changes** to trigger the CI workflow
3. **Verify the workflow passes** in GitHub Actions

## Step 5: Document Your Decision

When suppressing false positives, add a comment explaining why:

```toml
# GitLeaks example
[allowlist]
regexes = [
    # Suppressing UUID patterns as they're not secrets in our context
    '''[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}''',
]
```

## Best Practices

### ✅ Do:
- **Prefer specific suppressions** over broad ones
- **Document why** you're suppressing each pattern
- **Review suppressions periodically** to ensure they're still needed
- **Use environment variables** for real secrets
- **Test suppression rules** locally before committing

### ❌ Don't:
- **Suppress real secrets** - always remove them instead
- **Use overly broad patterns** that might miss real secrets
- **Suppress entire file types** unless absolutely necessary
- **Forget to rotate compromised secrets**

## Suppression Hierarchy

Use suppressions in this order of preference:

1. **File-specific patterns** (most precise)
2. **Regex patterns** for specific false positive types
3. **Path-based exclusions** for entire directories
4. **Commit-based suppression** (least preferred, use only for emergency fixes)

## Emergency Procedures

### If you've accidentally committed a real secret:

1. **Stop the deployment** immediately
2. **Rotate the secret** in the external service
3. **Remove the secret** from the codebase
4. **Consider rewriting git history** if the secret was recently added
5. **Update the suppression rules** if needed for any test fixtures

### If the CI is blocking critical deployments:

1. **Verify it's truly a false positive** by manual review
2. **Add a temporary commit-based suppression** with the commit hash
3. **Create a follow-up issue** to implement a proper pattern-based suppression
4. **Remove the temporary suppression** once the proper fix is in place

## Getting Help

If you're unsure whether a detection is a false positive:

1. **Review this documentation** first
2. **Check with the security team** for guidance
3. **Create an issue** describing the specific detection
4. **Include the scanner output** and your analysis

## Configuration Files Reference

- **`.gitleaks.toml`**: GitLeaks configuration and suppressions
- **`.trufflehog-exclude`**: TruffleHog exclusion patterns (one regex per line)
- **`.github/workflows/secret-scan.yml`**: GitHub Actions workflow
- **`docs/SECRET_SCAN_SUPPRESSION.md`**: This documentation

## Example Suppression Scenarios

### Scenario 1: Test Fixtures
```toml
# .gitleaks.toml
[allowlist]
files = [
    '''test/fixtures/.*''',
    '''tests/data/.*''',
]
```

### Scenario 2: Documentation Examples
```toml
# .gitleaks.toml
[allowlist]
regexes = [
    '''(?i)(password|secret|key|token)[[:space:]]*[:=][[:space:]]*["\']?(example|test|dummy|placeholder)["\']?''',
]
```

### Scenario 3: Configuration Templates
```
# .trufflehog-exclude
.*\.example$
.*\.template$
.*\.sample$
```

### Scenario 4: Specific False Positive Pattern
```toml
# .gitleaks.toml
[allowlist]
regexes = [
    # Our app generates IDs that look like secrets but aren't
    '''app_id_[a-f0-9]{32}''',
]
```

Remember: When in doubt, err on the side of caution and treat detections as real secrets until proven otherwise.
