# Unit Test Recommendations for Multi-Agent Observability System

## Executive Summary

This document outlines comprehensive unit test recommendations for the Claude Code Hooks Multi-Agent Observability project. The system currently lacks proper test coverage across all components, creating risks for maintainability, reliability, and continuous integration.

## Testing Framework & Tooling Recommendations

### Frontend (Vue.js Client)
- **Framework**: Vitest + Vue Test Utils
- **Mocking**: Pinia mocks for state management
- **Additional Tools**: 
  - @vue/test-utils for component testing
  - jsdom for DOM simulation
  - Mock Service Worker (MSW) for API mocking

### Backend (Bun Server)
- **Framework**: Bun test (native) or Vitest
- **HTTP Testing**: supertest-like assertions with `bun:test`
- **Database Testing**: In-memory SQLite for isolation
- **WebSocket Testing**: ws testing utilities

### Hooks (Python)
- **Framework**: Pytest with fixtures
- **HTTP Mocking**: responses library or httpx mock
- **File System Testing**: pytest-tmp-path for temporary directories

---

## 1. Frontend Testing Gaps & Recommendations

### 1.1 Component Testing

**Gap**: No unit tests for Vue components
**Coverage Target**: ≥85% component coverage

#### Critical Components to Test:

**EventTimeline.vue**
```typescript
// tests/components/EventTimeline.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import EventTimeline from '@/components/EventTimeline.vue'

describe('EventTimeline', () => {
  const mockEvents = [
    {
      id: 1,
      source_app: 'test-app',
      session_id: 'session-123',
      hook_event_type: 'PreToolUse',
      payload: { tool: 'Bash', command: 'ls' },
      timestamp: Date.now()
    }
  ]

  it('renders events correctly', () => {
    const wrapper = mount(EventTimeline, {
      props: { events: mockEvents, filters: {} }
    })
    
    expect(wrapper.find('[data-testid="event-item"]')).toBeTruthy()
    expect(wrapper.text()).toContain('PreToolUse')
  })

  it('filters events based on filters prop', () => {
    const filters = { eventType: 'PreToolUse' }
    const wrapper = mount(EventTimeline, {
      props: { events: mockEvents, filters }
    })
    
    // Assert filtered results
    expect(wrapper.findAll('[data-testid="event-item"]')).toHaveLength(1)
  })

  it('emits scroll events when stickToBottom changes', async () => {
    const wrapper = mount(EventTimeline, {
      props: { events: mockEvents, filters: {} }
    })
    
    await wrapper.setProps({ stickToBottom: false })
    expect(wrapper.emitted('update:stickToBottom')).toBeTruthy()
  })
})
```

**FilterPanel.vue**
```typescript
// tests/components/FilterPanel.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import FilterPanel from '@/components/FilterPanel.vue'

describe('FilterPanel', () => {
  const mockFilters = {
    sourceApp: '',
    sessionId: '',
    eventType: ''
  }

  it('displays filter controls', () => {
    const wrapper = mount(FilterPanel, {
      props: { filters: mockFilters }
    })
    
    expect(wrapper.find('select[data-testid="source-app-filter"]')).toBeTruthy()
    expect(wrapper.find('select[data-testid="session-id-filter"]')).toBeTruthy()
    expect(wrapper.find('select[data-testid="event-type-filter"]')).toBeTruthy()
  })

  it('emits filter updates', async () => {
    const wrapper = mount(FilterPanel, {
      props: { filters: mockFilters }
    })
    
    const select = wrapper.find('select[data-testid="source-app-filter"]')
    await select.setValue('test-app')
    
    expect(wrapper.emitted('update:filters')).toBeTruthy()
  })
})
```

**ThemeManager.vue**
```typescript
// tests/components/ThemeManager.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import ThemeManager from '@/components/ThemeManager.vue'

describe('ThemeManager', () => {
  it('opens and closes correctly', async () => {
    const wrapper = mount(ThemeManager, {
      props: { isOpen: false }
    })
    
    expect(wrapper.find('[data-testid="theme-modal"]').isVisible()).toBe(false)
    
    await wrapper.setProps({ isOpen: true })
    expect(wrapper.find('[data-testid="theme-modal"]').isVisible()).toBe(true)
  })

  it('switches between tabs', async () => {
    const wrapper = mount(ThemeManager, {
      props: { isOpen: true }
    })
    
    await wrapper.find('[data-testid="custom-tab"]').trigger('click')
    expect(wrapper.find('[data-testid="custom-theme-panel"]')).toBeTruthy()
  })
})
```

### 1.2 Composables Testing

**Gap**: No unit tests for Vue composables
**Coverage Target**: ≥90% composable coverage

#### useWebSocket.ts
```typescript
// tests/composables/useWebSocket.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useWebSocket } from '@/composables/useWebSocket'

// Mock WebSocket
const mockWebSocket = {
  send: vi.fn(),
  close: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn()
}

global.WebSocket = vi.fn(() => mockWebSocket)

describe('useWebSocket', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('initializes with correct default values', () => {
    const { events, isConnected, error } = useWebSocket('ws://localhost:4000')
    
    expect(events.value).toEqual([])
    expect(isConnected.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('handles initial message correctly', () => {
    const { events } = useWebSocket('ws://localhost:4000')
    
    const mockMessage = {
      type: 'initial',
      data: [{ id: 1, source_app: 'test' }]
    }
    
    // Simulate WebSocket message
    mockWebSocket.onmessage({ data: JSON.stringify(mockMessage) })
    
    expect(events.value).toEqual(mockMessage.data)
  })

  it('handles connection errors', () => {
    const { error } = useWebSocket('ws://localhost:4000')
    
    mockWebSocket.onerror(new Error('Connection failed'))
    
    expect(error.value).toBe('WebSocket connection error')
  })
})
```

#### useThemes.ts
```typescript
// tests/composables/useThemes.spec.ts
import { describe, it, expect, vi } from 'vitest'
import { useThemes } from '@/composables/useThemes'

describe('useThemes', () => {
  it('initializes with default light theme', () => {
    const { state } = useThemes()
    
    expect(state.currentTheme).toBe('light')
    expect(state.isCustomTheme).toBe(false)
  })

  it('validates theme colors correctly', () => {
    const { validateTheme } = useThemes()
    
    const validColors = {
      primary: '#3b82f6',
      primaryHover: '#2563eb',
      bgPrimary: '#ffffff'
    }
    
    const result = validateTheme(validColors)
    expect(result.isValid).toBe(true)
  })

  it('creates custom theme successfully', async () => {
    const { createCustomTheme } = useThemes()
    
    const formData = {
      name: 'test-theme',
      displayName: 'Test Theme',
      colors: { /* valid colors */ },
      isPublic: false
    }
    
    const theme = await createCustomTheme(formData)
    expect(theme).toBeTruthy()
    expect(theme.name).toBe('test-theme')
  })
})
```

### 1.3 Utility Testing

**Gap**: No tests for utility functions
**Coverage Target**: ≥95% utility coverage

#### chartRenderer.ts
```typescript
// tests/utils/chartRenderer.spec.ts
import { describe, it, expect } from 'vitest'
import { renderChart, calculateChartData } from '@/utils/chartRenderer'

describe('chartRenderer', () => {
  it('processes event data correctly', () => {
    const events = [
      { hook_event_type: 'PreToolUse', timestamp: 1000 },
      { hook_event_type: 'PostToolUse', timestamp: 2000 }
    ]
    
    const result = calculateChartData(events)
    
    expect(result).toHaveLength(2)
    expect(result[0].type).toBe('PreToolUse')
  })

  it('handles empty event array', () => {
    const result = calculateChartData([])
    expect(result).toEqual([])
  })
})
```

### 1.4 Package.json Updates

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  },
  "devDependencies": {
    "@vue/test-utils": "^2.4.0",
    "vitest": "^1.0.0",
    "@vitest/ui": "^1.0.0",
    "jsdom": "^23.0.0",
    "msw": "^2.0.0"
  }
}
```

---

## 2. Backend Testing Gaps & Recommendations

### 2.1 API Endpoint Testing

**Gap**: No API endpoint tests
**Coverage Target**: ≥90% endpoint coverage

#### Server Integration Tests
```typescript
// tests/server/endpoints.test.ts
import { describe, it, expect, beforeEach, afterEach } from 'bun:test'
import { HookEvent } from '../src/types'

describe('Server Endpoints', () => {
  const baseUrl = 'http://localhost:4000'
  
  beforeEach(() => {
    // Setup test database
  })

  afterEach(() => {
    // Cleanup test database
  })

  describe('POST /events', () => {
    it('accepts valid hook events', async () => {
      const event: HookEvent = {
        source_app: 'test-app',
        session_id: 'test-session',
        hook_event_type: 'PreToolUse',
        payload: { tool: 'Bash', command: 'ls' }
      }

      const response = await fetch(`${baseUrl}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(event)
      })

      expect(response.status).toBe(200)
      const result = await response.json()
      expect(result.id).toBeDefined()
    })

    it('rejects invalid events', async () => {
      const invalidEvent = {
        source_app: 'test-app'
        // Missing required fields
      }

      const response = await fetch(`${baseUrl}/events`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(invalidEvent)
      })

      expect(response.status).toBe(400)
    })
  })

  describe('GET /events/recent', () => {
    it('returns recent events', async () => {
      const response = await fetch(`${baseUrl}/events/recent?limit=10`)
      
      expect(response.status).toBe(200)
      const events = await response.json()
      expect(Array.isArray(events)).toBe(true)
    })
  })
})
```

### 2.2 Database Layer Testing

**Gap**: No database operation tests
**Coverage Target**: ≥85% database coverage

#### Database Operations
```typescript
// tests/db/operations.test.ts
import { describe, it, expect, beforeEach } from 'bun:test'
import { Database } from 'bun:sqlite'
import { initDatabase, insertEvent, getRecentEvents } from '../src/db'

describe('Database Operations', () => {
  let testDb: Database

  beforeEach(() => {
    testDb = new Database(':memory:')
    // Use test database for operations
  })

  describe('insertEvent', () => {
    it('inserts event successfully', () => {
      const event = {
        source_app: 'test-app',
        session_id: 'test-session',
        hook_event_type: 'PreToolUse',
        payload: { tool: 'Bash' }
      }

      const result = insertEvent(event)
      
      expect(result.id).toBeDefined()
      expect(result.timestamp).toBeDefined()
    })

    it('handles malformed payload', () => {
      const event = {
        source_app: 'test-app',
        session_id: 'test-session',
        hook_event_type: 'PreToolUse',
        payload: null
      }

      expect(() => insertEvent(event)).toThrow()
    })
  })

  describe('getRecentEvents', () => {
    it('returns events in reverse chronological order', () => {
      // Insert test events
      const events = getRecentEvents(10)
      
      expect(events.length).toBeLessThanOrEqual(10)
      // Check ordering
      for (let i = 1; i < events.length; i++) {
        expect(events[i].timestamp).toBeGreaterThan(events[i-1].timestamp)
      }
    })
  })
})
```

### 2.3 WebSocket Testing

**Gap**: No WebSocket functionality tests
**Coverage Target**: ≥80% WebSocket coverage

#### WebSocket Connection Tests
```typescript
// tests/websocket/connection.test.ts
import { describe, it, expect } from 'bun:test'
import { WebSocket } from 'ws'

describe('WebSocket Connection', () => {
  it('accepts WebSocket connections', (done) => {
    const ws = new WebSocket('ws://localhost:4000/stream')
    
    ws.on('open', () => {
      expect(ws.readyState).toBe(WebSocket.OPEN)
      ws.close()
      done()
    })
  })

  it('sends initial events on connection', (done) => {
    const ws = new WebSocket('ws://localhost:4000/stream')
    
    ws.on('message', (data) => {
      const message = JSON.parse(data.toString())
      expect(message.type).toBe('initial')
      expect(Array.isArray(message.data)).toBe(true)
      ws.close()
      done()
    })
  })

  it('broadcasts new events to all clients', (done) => {
    const ws1 = new WebSocket('ws://localhost:4000/stream')
    const ws2 = new WebSocket('ws://localhost:4000/stream')
    
    let connections = 0
    const checkConnection = () => {
      connections++
      if (connections === 2) {
        // Send test event
        fetch('http://localhost:4000/events', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source_app: 'test',
            session_id: 'test',
            hook_event_type: 'Test',
            payload: {}
          })
        })
      }
    }
    
    ws1.on('open', checkConnection)
    ws2.on('open', checkConnection)
    
    ws1.on('message', (data) => {
      const message = JSON.parse(data.toString())
      if (message.type === 'event') {
        expect(message.data.hook_event_type).toBe('Test')
        ws1.close()
        ws2.close()
        done()
      }
    })
  })
})
```

### 2.4 Theme API Testing

**Gap**: No theme management tests
**Coverage Target**: ≥85% theme API coverage

#### Theme Management Tests
```typescript
// tests/theme/api.test.ts
import { describe, it, expect } from 'bun:test'
import { createTheme, getThemeById, updateThemeById } from '../src/theme'

describe('Theme API', () => {
  describe('createTheme', () => {
    it('creates theme successfully', async () => {
      const themeData = {
        name: 'test-theme',
        displayName: 'Test Theme',
        colors: { primary: '#000000' },
        isPublic: false
      }

      const result = await createTheme(themeData)
      
      expect(result.success).toBe(true)
      expect(result.data.id).toBeDefined()
    })

    it('validates required fields', async () => {
      const result = await createTheme({})
      
      expect(result.success).toBe(false)
      expect(result.error).toContain('required')
    })
  })
})
```

---

## 3. Python Hooks Testing Gaps & Recommendations

### 3.1 Hook Event Processing

**Gap**: No tests for hook event processing
**Coverage Target**: ≥85% hook coverage

#### Hook Event Tests
```python
# tests/test_hook_events.py
import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'hooks'))

from utils.constants import get_session_log_dir, ensure_session_log_dir

class TestHookEvents:
    @pytest.fixture
    def mock_session_id(self):
        return "test-session-123"
    
    @pytest.fixture
    def temp_log_dir(self, tmp_path):
        return tmp_path / "logs"
    
    def test_get_session_log_dir(self, mock_session_id):
        """Test session log directory path generation"""
        log_dir = get_session_log_dir(mock_session_id)
        assert str(log_dir).endswith(mock_session_id)
        assert log_dir.name == mock_session_id
    
    def test_ensure_session_log_dir(self, mock_session_id, tmp_path, monkeypatch):
        """Test session log directory creation"""
        monkeypatch.setenv("CLAUDE_HOOKS_LOG_DIR", str(tmp_path))
        
        log_dir = ensure_session_log_dir(mock_session_id)
        assert log_dir.exists()
        assert log_dir.is_dir()
    
    @patch('requests.post')
    def test_send_event_success(self, mock_post):
        """Test successful event sending"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"id": 123}
        
        from send_event import send_hook_event
        
        result = send_hook_event(
            source_app="test-app",
            session_id="test-session",
            event_type="PreToolUse",
            payload={"tool": "Bash", "command": "ls"}
        )
        
        assert result is not None
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_send_event_failure(self, mock_post):
        """Test event sending failure handling"""
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = "Bad Request"
        
        from send_event import send_hook_event
        
        result = send_hook_event(
            source_app="test-app",
            session_id="test-session", 
            event_type="InvalidEvent",
            payload={}
        )
        
        assert result is None
    
    @patch('requests.post')
    def test_send_event_timeout(self, mock_post):
        """Test event sending timeout handling"""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        from send_event import send_hook_event
        
        result = send_hook_event(
            source_app="test-app",
            session_id="test-session",
            event_type="PreToolUse",
            payload={"tool": "Bash"}
        )
        
        assert result is None
```

### 3.2 File System Event Monitoring

**Gap**: No tests for file system monitoring
**Coverage Target**: ≥80% monitoring coverage

#### File System Tests
```python
# tests/test_hook_forwarder.py
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from hook_event_forwarder import HookEventHandler

class TestHookEventForwarder:
    @pytest.fixture
    def temp_project_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            hooks_dir = temp_path / '.claude' / 'hooks'
            hooks_dir.mkdir(parents=True)
            
            # Create mock send_event.py
            send_event_script = hooks_dir / 'send_event.py'
            send_event_script.write_text('''
import sys
import json
print(json.dumps({"status": "success"}))
''')
            
            yield temp_path
    
    @pytest.fixture
    def event_handler(self, temp_project_dir):
        return HookEventHandler(temp_project_dir)
    
    def test_handler_initialization(self, event_handler, temp_project_dir):
        """Test event handler initialization"""
        assert event_handler.project_root == temp_project_dir
        assert event_handler.hooks_dir == temp_project_dir / '.claude' / 'hooks'
        assert event_handler.logs_dir.exists()
    
    @patch('subprocess.Popen')
    def test_handle_python_file_event(self, mock_popen, event_handler, temp_project_dir):
        """Test handling of Python file events"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = ('{"status": "success"}', '')
        mock_popen.return_value = mock_process
        
        test_file = temp_project_dir / '.claude' / 'hooks' / 'test_hook.py'
        test_file.write_text('print("test")')
        
        event_handler.handle_event('created', str(test_file))
        
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        assert 'send_event.py' in ' '.join(args[0])
    
    def test_ignore_non_python_files(self, event_handler, temp_project_dir):
        """Test that non-Python files are ignored"""
        test_file = temp_project_dir / '.claude' / 'hooks' / 'test.txt'
        test_file.write_text('test content')
        
        with patch.object(event_handler, 'forward_hook_event') as mock_forward:
            event_handler.handle_event('created', str(test_file))
            mock_forward.assert_not_called()
    
    def test_ignore_files_outside_hooks_dir(self, event_handler, temp_project_dir):
        """Test that files outside hooks directory are ignored"""
        test_file = temp_project_dir / 'test.py'
        test_file.write_text('print("test")')
        
        with patch.object(event_handler, 'forward_hook_event') as mock_forward:
            event_handler.handle_event('created', str(test_file))
            mock_forward.assert_not_called()
```

### 3.3 LLM Integration Testing

**Gap**: No tests for LLM utilities
**Coverage Target**: ≥75% LLM integration coverage

#### LLM Tests
```python
# tests/test_llm_integration.py
import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / '.claude' / 'hooks' / 'utils' / 'llm'))

from anth import generate_summary
from oai import generate_openai_summary

class TestLLMIntegration:
    @patch('anth.anthropic.Anthropic')
    def test_anthropic_summary_generation(self, mock_anthropic):
        """Test Anthropic summary generation"""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test summary")]
        mock_client.messages.create.return_value = mock_response
        
        result = generate_summary("Test event data")
        
        assert result == "Test summary"
        mock_client.messages.create.assert_called_once()
    
    @patch('openai.OpenAI')
    def test_openai_summary_generation(self, mock_openai):
        """Test OpenAI summary generation"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Test summary"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = generate_openai_summary("Test event data")
        
        assert result == "Test summary"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('anth.anthropic.Anthropic')
    def test_anthropic_api_error_handling(self, mock_anthropic):
        """Test Anthropic API error handling"""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")
        
        result = generate_summary("Test event data")
        
        assert result is None or result == "Error generating summary"
```

### 3.4 pytest.ini Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --strict-markers
    --tb=short
    --cov=.claude/hooks
    --cov=scripts
    --cov-report=html
    --cov-report=term-missing
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

---

## 4. Coverage Targets & Quality Gates

### 4.1 Coverage Targets

| Component | Target Coverage | Priority |
|-----------|-----------------|----------|
| Frontend Components | ≥85% | High |
| Frontend Composables | ≥90% | High |
| Frontend Utilities | ≥95% | Medium |
| Backend API Endpoints | ≥90% | High |
| Backend Database Layer | ≥85% | High |
| Backend WebSocket | ≥80% | Medium |
| Python Hooks | ≥85% | High |
| Python Utilities | ≥90% | Medium |

### 4.2 Critical Path Testing Priority

1. **Highest Priority** (Must have ≥95% coverage):
   - Event ingestion and processing
   - WebSocket real-time communication
   - Database operations (CRUD)
   - Hook event forwarding

2. **High Priority** (Must have ≥85% coverage):
   - Vue component rendering
   - Theme management
   - Filter functionality
   - Error handling

3. **Medium Priority** (Must have ≥75% coverage):
   - UI interactions
   - File system monitoring
   - LLM integrations
   - Configuration management

---

## 5. Continuous Integration Integration

### 5.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - name: Install dependencies
        run: npm ci
        working-directory: ./apps/client
      - name: Run frontend tests
        run: npm run test:coverage
        working-directory: ./apps/client
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3

  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: oven-sh/setup-bun@v1
        with:
          bun-version: latest
      - name: Install dependencies
        run: bun install
        working-directory: ./apps/server
      - name: Run backend tests
        run: bun test --coverage
        working-directory: ./apps/server

  python-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov responses
      - name: Run Python tests
        run: pytest --cov=.claude/hooks --cov=scripts --cov-report=xml
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

### 5.2 Quality Gates

```yaml
# .github/workflows/quality-gates.yml
name: Quality Gates

on:
  pull_request:
    branches: [ main ]

jobs:
  coverage-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check coverage thresholds
        run: |
          # Frontend coverage check
          cd apps/client
          npm run test:coverage
          if [ $(npx nyc report --reporter=json | jq '.total.lines.pct') -lt 85 ]; then
            echo "Frontend coverage below 85%"
            exit 1
          fi
          
          # Backend coverage check
          cd ../server
          bun test --coverage
          # Add coverage threshold check for Bun
          
          # Python coverage check
          cd ../..
          pytest --cov=.claude/hooks --cov=scripts --cov-fail-under=85
```

---

## 6. Test Data & Fixtures

### 6.1 Frontend Test Data

```typescript
// tests/fixtures/events.ts
export const mockEvents = [
  {
    id: 1,
    source_app: 'test-app',
    session_id: 'session-123',
    hook_event_type: 'PreToolUse',
    payload: {
      tool: 'Bash',
      command: 'ls -la',
      args: ['-la']
    },
    timestamp: 1640995200000
  },
  {
    id: 2,
    source_app: 'test-app',
    session_id: 'session-123',
    hook_event_type: 'PostToolUse',
    payload: {
      tool: 'Bash',
      output: 'total 0\ndrwxr-xr-x 1 user user 0 Jan 1 12:00 .',
      success: true
    },
    timestamp: 1640995201000
  }
]

export const mockTheme = {
  id: 'test-theme-123',
  name: 'test-theme',
  displayName: 'Test Theme',
  colors: {
    primary: '#3b82f6',
    primaryHover: '#2563eb',
    bgPrimary: '#ffffff',
    textPrimary: '#111827'
  },
  isCustom: true
}
```

### 6.2 Backend Test Data

```typescript
// tests/fixtures/database.ts
export const createTestDatabase = () => {
  const db = new Database(':memory:')
  
  // Initialize schema
  db.exec(`
    CREATE TABLE events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_app TEXT NOT NULL,
      session_id TEXT NOT NULL,
      hook_event_type TEXT NOT NULL,
      payload TEXT NOT NULL,
      timestamp INTEGER NOT NULL
    )
  `)
  
  return db
}

export const seedTestData = (db: Database) => {
  const stmt = db.prepare(`
    INSERT INTO events (source_app, session_id, hook_event_type, payload, timestamp)
    VALUES (?, ?, ?, ?, ?)
  `)
  
  stmt.run('test-app', 'session-1', 'PreToolUse', '{"tool":"Bash"}', Date.now())
  stmt.run('test-app', 'session-1', 'PostToolUse', '{"success":true}', Date.now() + 1000)
}
```

### 6.3 Python Test Fixtures

```python
# tests/fixtures/hooks.py
import pytest
import tempfile
import json
from pathlib import Path

@pytest.fixture
def mock_session_data():
    return {
        "session_id": "test-session-123",
        "source_app": "test-app",
        "events": [
            {
                "hook_event_type": "PreToolUse",
                "payload": {
                    "tool": "Bash",
                    "command": "ls -la"
                },
                "timestamp": 1640995200000
            }
        ]
    }

@pytest.fixture
def temp_hooks_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        hooks_dir = temp_path / '.claude' / 'hooks'
        hooks_dir.mkdir(parents=True)
        
        # Create mock send_event.py
        send_event_script = hooks_dir / 'send_event.py'
        send_event_script.write_text('''
import sys
import json

def send_hook_event(source_app, session_id, event_type, payload):
    return {"id": 123, "status": "success"}

if __name__ == "__main__":
    print(json.dumps({"status": "success"}))
        ''')
        
        yield temp_path

@pytest.fixture
def mock_http_responses():
    """Mock HTTP responses for testing"""
    return {
        "success": {
            "status_code": 200,
            "json": {"id": 123, "status": "success"}
        },
        "error": {
            "status_code": 400,
            "text": "Bad Request"
        }
    }
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Set up testing frameworks (Vitest, Bun test, pytest)
- [ ] Create basic test structure and fixtures
- [ ] Implement critical path tests (event processing, WebSocket)
- [ ] Set up CI/CD pipeline with basic coverage

### Phase 2: Core Features (Weeks 3-4)
- [ ] Complete frontend component tests
- [ ] Implement backend API endpoint tests
- [ ] Add Python hook event tests
- [ ] Achieve 80% coverage on critical paths

### Phase 3: Comprehensive Coverage (Weeks 5-6)
- [ ] Complete composable and utility tests
- [ ] Add integration tests
- [ ] Implement theme management tests
- [ ] Achieve target coverage levels

### Phase 4: Quality Assurance (Weeks 7-8)
- [ ] Add performance tests
- [ ] Implement error scenario tests
- [ ] Add accessibility tests for components
- [ ] Final coverage optimization

---

## 8. Maintenance & Best Practices

### 8.1 Test Maintenance
- Run tests on every commit
- Update tests when adding new features
- Regular test review and cleanup
- Monitor coverage trends

### 8.2 Testing Best Practices
- Write tests before implementing features (TDD)
- Use descriptive test names
- Keep tests isolated and independent
- Mock external dependencies
- Test both success and failure scenarios

### 8.3 Documentation
- Document test setup and conventions
- Maintain test data documentation
- Keep fixture documentation updated
- Document complex test scenarios

---

## Conclusion

This comprehensive unit testing strategy addresses all major gaps in the Multi-Agent Observability System. By implementing these recommendations, the project will achieve:

- **Reliability**: Comprehensive test coverage ensures system stability
- **Maintainability**: Tests provide safety net for refactoring
- **Quality**: Automated quality gates prevent regressions
- **Confidence**: Developers can make changes with confidence
- **Documentation**: Tests serve as living documentation

The phased implementation approach allows for gradual adoption while maintaining development velocity. Priority should be given to critical paths and high-risk areas, with comprehensive coverage following in subsequent phases.
