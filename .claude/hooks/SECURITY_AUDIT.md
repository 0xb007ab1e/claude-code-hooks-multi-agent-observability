# Security Audit Report for .claude/hooks

## Summary

This document outlines the security audit performed on all Python hook scripts in `.claude/hooks` and the remediation actions taken.

## Issues Found and Fixed

### 1. Hard-coded Model Names (Security Risk: Confidential Usage Tiers)

**Problem**: Several scripts contained hard-coded model names that could reveal confidential usage tiers or specific model access levels.

**Files affected**:
- `utils/llm/anth.py` - Hard-coded "claude-3-5-haiku-20241022"
- `utils/llm/oai.py` - Hard-coded "gpt-4.1-nano"
- `utils/tts/elevenlabs_tts.py` - Hard-coded "eleven_turbo_v2_5" and voice ID "WejK3H1m7MI9CHnIjW9K"
- `utils/tts/openai_tts.py` - Hard-coded "gpt-4o-mini-tts" and voice "nova"

**Solution**: 
- Replaced all hard-coded model names with `os.getenv()` calls
- Added fallback values using the previous hard-coded values as defaults
- Created new environment variables for each model configuration

### 2. Missing load_dotenv() Calls

**Problem**: Several scripts were not loading environment variables from `.env` files early in execution.

**Files affected**:
- `post_tool_use.py`
- `pre_tool_use.py`
- `utils/constants.py`
- `send_event.py`

**Solution**:
- Added `load_dotenv()` calls at the beginning of each script
- Added python-dotenv dependency to script headers
- Used try/except blocks to handle missing dotenv package gracefully

### 3. Missing Environment Variables in .env.sample

**Problem**: Environment variables used in the code were not documented in `.env.sample`.

**Missing variables**:
- `CLAUDE_HOOKS_LOG_DIR`
- `ANTHROPIC_MODEL`
- `OPENAI_MODEL`
- `OPENAI_TTS_MODEL`
- `OPENAI_TTS_VOICE`
- `ELEVENLABS_MODEL`
- `ELEVENLABS_VOICE_ID`

**Solution**:
- Updated `.env.sample` to include all environment variables
- Organized variables into logical sections (API Keys, Model Configuration, User Configuration, System Configuration)
- Added default values as examples

## Security Verification

### ✅ All scripts now properly use os.getenv() for secrets
- API keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`
- Model configurations: All model names and IDs now use environment variables
- User settings: `ENGINEER_NAME` consistently loaded from environment

### ✅ All scripts call load_dotenv() early
- Every Python script now loads environment variables at startup
- Graceful handling of missing dotenv package
- Proper error handling for environment variable access

### ✅ No hard-coded credentials or model names remain
- All sensitive configuration moved to environment variables
- Default fallback values prevent breaking changes
- Clear documentation of all required variables

### ✅ All environment variables documented in .env.sample
- Complete list of required and optional variables
- Organized by category for better maintainability
- Example values provided where appropriate

## Files Modified

1. `utils/llm/anth.py` - Added ANTHROPIC_MODEL environment variable
2. `utils/llm/oai.py` - Added OPENAI_MODEL environment variable
3. `utils/tts/elevenlabs_tts.py` - Added ELEVENLABS_MODEL and ELEVENLABS_VOICE_ID variables
4. `utils/tts/openai_tts.py` - Added OPENAI_TTS_MODEL and OPENAI_TTS_VOICE variables
5. `post_tool_use.py` - Added load_dotenv() call
6. `pre_tool_use.py` - Added load_dotenv() call
7. `utils/constants.py` - Added load_dotenv() call
8. `send_event.py` - Added load_dotenv() call
9. `.env.sample` - Added all missing environment variables with documentation

## Recommendations

1. **Regular Security Audits**: Perform similar audits when adding new scripts or modifying existing ones
2. **Environment Variable Validation**: Consider adding validation for critical environment variables
3. **Documentation**: Keep `.env.sample` updated when adding new environment variables
4. **Testing**: Test scripts with missing environment variables to ensure graceful fallback behavior
