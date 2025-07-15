#!/bin/bash

echo "🔒 Security Testing Suite"
echo "========================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo -e "\n${GREEN}1. Running git-secrets scan...${NC}"
cd "$PROJECT_ROOT"
git secrets --scan

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ No secrets found in repository${NC}"
else
    echo -e "${RED}❌ Secrets detected in repository${NC}"
    echo "Please review and remove any exposed credentials"
fi

echo -e "\n${GREEN}2. Checking environment variable usage...${NC}"
echo "Scanning for hardcoded credentials..."

# Check for hardcoded API keys
if grep -r "sk-ant-api03-" . --exclude-dir=node_modules --exclude-dir=.git; then
    echo -e "${RED}❌ Found hardcoded Anthropic API key${NC}"
else
    echo -e "${GREEN}✅ No hardcoded Anthropic API keys found${NC}"
fi

if grep -r "sk-proj-" . --exclude-dir=node_modules --exclude-dir=.git; then
    echo -e "${RED}❌ Found hardcoded OpenAI API key${NC}"
else
    echo -e "${GREEN}✅ No hardcoded OpenAI API keys found${NC}"
fi

echo -e "\n${GREEN}3. Checking for .env files in git...${NC}"
if git ls-files | grep -E '\.env$|\.env\..*'; then
    echo -e "${RED}❌ .env files found in repository${NC}"
    echo "These files may contain sensitive information"
else
    echo -e "${GREEN}✅ No .env files tracked in git${NC}"
fi

echo -e "\n${GREEN}4. Validating environment variable configuration...${NC}"
# Check if .env.sample exists
if [ -f ".env.sample" ]; then
    echo -e "${GREEN}✅ .env.sample file exists${NC}"
else
    echo -e "${YELLOW}⚠️ .env.sample file missing${NC}"
fi

# Check if .env exists
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
else
    echo -e "${YELLOW}⚠️ .env file missing${NC}"
fi

echo -e "\n${GREEN}5. Checking Python hook security...${NC}"
# Check for proper environment variable usage in Python hooks
if find . -name "*.py" -path "*/.claude/hooks/*" -exec grep -l "getenv\|load_dotenv" {} \; | wc -l | grep -q "0"; then
    echo -e "${YELLOW}⚠️ Some Python hooks may not be using environment variables${NC}"
else
    echo -e "${GREEN}✅ Python hooks using environment variables${NC}"
fi

echo -e "\n${GREEN}6. File permissions check...${NC}"
# Check for overly permissive files
if find . -name "*.py" -perm 777 2>/dev/null | head -1; then
    echo -e "${RED}❌ Found files with 777 permissions${NC}"
else
    echo -e "${GREEN}✅ No overly permissive files found${NC}"
fi

echo -e "\n${GREEN}7. Dependency security check...${NC}"
# Check for npm audit
if [ -f "apps/client/package.json" ]; then
    echo "Checking client dependencies..."
    cd "apps/client"
    npm audit --audit-level=moderate
    cd "$PROJECT_ROOT"
fi

echo -e "\n${GREEN}Security scan complete!${NC}"
echo "For a comprehensive security audit, consider running:"
echo "  - OWASP ZAP against the running application"
echo "  - Static analysis tools like Semgrep or CodeQL"
echo "  - Container scanning if using Docker"
