# Comprehensive Unit Test Plan

## Overview
This document maps each unchecked behavior in the FastAPI multi-agent observability server to comprehensive unit tests. The test plan ensures 100% coverage of all branches, conditionals, and edge cases.

## Test Categories

### 1. FastAPI Route Tests via TestClient

#### 1.1 Root Endpoint Tests
- **Test Case**: `test_root_endpoint`
  - **Behavior**: GET `/` returns server message
  - **Expected**: Status 200, correct message format

#### 1.2 Health Check Tests
- **Test Case**: `test_health_check_endpoint`
  - **Behavior**: GET `/health` returns health status
  - **Expected**: Status 200, "healthy" status, ISO timestamp

#### 1.3 Events CRUD Tests
- **Test Case**: `test_create_event_success`
  - **Behavior**: POST `/events` with valid data
  - **Expected**: Status 200, event created with ID and timestamp

- **Test Case**: `test_create_event_missing_fields`
  - **Behavior**: POST `/events` with missing required fields
  - **Expected**: Status 400, validation error details

- **Test Case**: `test_create_event_invalid_payload`
  - **Behavior**: POST `/events` with invalid JSON payload
  - **Expected**: Status 400, validation error

- **Test Case**: `test_get_recent_events_default`
  - **Behavior**: GET `/events/recent` with default pagination
  - **Expected**: Status 200, list of events (max 100)

- **Test Case**: `test_get_recent_events_with_pagination`
  - **Behavior**: GET `/events/recent?limit=10&offset=5`
  - **Expected**: Status 200, correct pagination applied

- **Test Case**: `test_get_filter_options`
  - **Behavior**: GET `/events/filter-options`
  - **Expected**: Status 200, FilterOptions with all arrays

- **Test Case**: `test_get_event_count`
  - **Behavior**: GET `/events/count`
  - **Expected**: Status 200, EventCount with integer value

#### 1.4 Theme API Tests
- **Test Case**: `test_create_theme_success`
  - **Behavior**: POST `/api/themes` with valid theme data
  - **Expected**: Status 201, theme created successfully

- **Test Case**: `test_create_theme_duplicate_id`
  - **Behavior**: POST `/api/themes` with existing ID
  - **Expected**: Status 400, duplicate error

- **Test Case**: `test_create_theme_invalid_colors`
  - **Behavior**: POST `/api/themes` with invalid color format
  - **Expected**: Status 400, validation error

- **Test Case**: `test_get_theme_stats`
  - **Behavior**: GET `/api/themes/stats`
  - **Expected**: Status 200, stats object with totals

- **Test Case**: `test_search_themes_no_params`
  - **Behavior**: GET `/api/themes` with no query parameters
  - **Expected**: Status 200, default search results

- **Test Case**: `test_search_themes_with_query`
  - **Behavior**: GET `/api/themes?query=dark&sortBy=name`
  - **Expected**: Status 200, filtered and sorted results

- **Test Case**: `test_search_themes_public_only`
  - **Behavior**: GET `/api/themes?isPublic=true`
  - **Expected**: Status 200, only public themes

- **Test Case**: `test_get_theme_by_id_exists`
  - **Behavior**: GET `/api/themes/{valid_id}`
  - **Expected**: Status 200, theme details

- **Test Case**: `test_get_theme_by_id_not_found`
  - **Behavior**: GET `/api/themes/{invalid_id}`
  - **Expected**: Status 404, not found error

- **Test Case**: `test_get_theme_empty_id`
  - **Behavior**: GET `/api/themes/`
  - **Expected**: Status 400, ID required error

#### 1.5 WebSocket Tests
- **Test Case**: `test_websocket_connection`
  - **Behavior**: Connect to `/stream` WebSocket
  - **Expected**: Connection accepted, initial data sent

- **Test Case**: `test_websocket_broadcast_on_event`
  - **Behavior**: Create event, verify WebSocket broadcast
  - **Expected**: Connected clients receive event broadcast

- **Test Case**: `test_websocket_disconnect_cleanup`
  - **Behavior**: Disconnect WebSocket, verify cleanup
  - **Expected**: Connection removed from active set

#### 1.6 CORS and Options Tests
- **Test Case**: `test_options_events_endpoint`
  - **Behavior**: OPTIONS `/events`
  - **Expected**: Status 200, CORS headers present

- **Test Case**: `test_cors_headers`
  - **Behavior**: Any request with CORS validation
  - **Expected**: Proper CORS headers in response

#### 1.7 Catch-all Handler Tests
- **Test Case**: `test_catch_all_handler`
  - **Behavior**: GET `/nonexistent/path`
  - **Expected**: Status 200, default message

### 2. Model Serialization/Deserialization Edge Cases

#### 2.1 HookEvent Model Tests
- **Test Case**: `test_hook_event_minimal_data`
  - **Behavior**: Create HookEvent with only required fields
  - **Expected**: Valid model, auto-generated timestamp

- **Test Case**: `test_hook_event_full_data`
  - **Behavior**: Create HookEvent with all fields
  - **Expected**: All fields correctly serialized

- **Test Case**: `test_hook_event_invalid_timestamp`
  - **Behavior**: Create HookEvent with invalid timestamp type
  - **Expected**: Validation error

- **Test Case**: `test_hook_event_empty_payload`
  - **Behavior**: Create HookEvent with empty dict payload
  - **Expected**: Valid model (empty dict is valid)

- **Test Case**: `test_hook_event_none_payload`
  - **Behavior**: Create HookEvent with None payload
  - **Expected**: Validation error (payload required)

- **Test Case**: `test_hook_event_complex_payload`
  - **Behavior**: Create HookEvent with nested dict/list payload
  - **Expected**: Complex data correctly serialized

#### 2.2 Theme Model Tests
- **Test Case**: `test_theme_model_required_fields`
  - **Behavior**: Create Theme with missing required fields
  - **Expected**: Validation error for each missing field

- **Test Case**: `test_theme_colors_validation`
  - **Behavior**: Create Theme with invalid color values
  - **Expected**: Validation error for color format

- **Test Case**: `test_theme_optional_fields_defaults`
  - **Behavior**: Create Theme without optional fields
  - **Expected**: Default values applied correctly

- **Test Case**: `test_theme_serialization_roundtrip`
  - **Behavior**: Create Theme, serialize to dict, deserialize back
  - **Expected**: Original data preserved

#### 2.3 Filter and Response Model Tests
- **Test Case**: `test_filter_options_empty_lists`
  - **Behavior**: Create FilterOptions with empty lists
  - **Expected**: Valid model with empty arrays

- **Test Case**: `test_api_response_success`
  - **Behavior**: Create ApiResponse with success=True
  - **Expected**: Correct serialization

- **Test Case**: `test_api_response_error`
  - **Behavior**: Create ApiResponse with error details
  - **Expected**: Error fields properly serialized

### 3. Config Precedence Testing

#### 3.1 Environment Variable Override Tests
- **Test Case**: `test_config_defaults`
  - **Behavior**: Load config without env vars
  - **Expected**: Default values used

- **Test Case**: `test_config_env_override_port`
  - **Behavior**: Set PORT env var, load config
  - **Expected**: Env var value overrides default

- **Test Case**: `test_config_env_override_database_path`
  - **Behavior**: Set DATABASE_PATH env var
  - **Expected**: Custom path used

- **Test Case**: `test_config_cors_origins_single`
  - **Behavior**: Set CORS_ORIGINS to single domain
  - **Expected**: Single domain in list

- **Test Case**: `test_config_cors_origins_multiple`
  - **Behavior**: Set CORS_ORIGINS to comma-separated list
  - **Expected**: Multiple domains parsed correctly

- **Test Case**: `test_config_cors_origins_wildcard`
  - **Behavior**: Set CORS_ORIGINS to "*"
  - **Expected**: Wildcard preserved as ["*"]

#### 3.2 Production Configuration Tests
- **Test Case**: `test_production_config_validation_success`
  - **Behavior**: Set ENVIRONMENT=production with required vars
  - **Expected**: Validation passes

- **Test Case**: `test_production_config_validation_failure`
  - **Behavior**: Set ENVIRONMENT=production without DATABASE_PATH
  - **Expected**: ValueError raised

- **Test Case**: `test_development_config_lenient`
  - **Behavior**: Development mode with missing optional vars
  - **Expected**: No validation errors

#### 3.3 Optional Configuration Tests
- **Test Case**: `test_optional_postgres_config`
  - **Behavior**: Set POSTGRES_URL and related vars
  - **Expected**: Config loaded correctly

- **Test Case**: `test_optional_auth_config`
  - **Behavior**: Set API_KEY and JWT_SECRET
  - **Expected**: Auth config available

- **Test Case**: `test_rate_limit_config`
  - **Behavior**: Set rate limiting parameters
  - **Expected**: Custom limits applied

### 4. Database Session Lifecycle & Error Paths

#### 4.1 In-Memory SQLite Fixture
```python
@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing"""
    from database import Database
    db = Database(":memory:")
    yield db
    # Cleanup handled by memory disposal
```

#### 4.2 Database Connection Tests
- **Test Case**: `test_database_init_creates_tables`
  - **Behavior**: Initialize database
  - **Expected**: All tables and indexes created

- **Test Case**: `test_database_init_idempotent`
  - **Behavior**: Initialize database multiple times
  - **Expected**: No errors, tables remain consistent

#### 4.3 Event Database Tests
- **Test Case**: `test_insert_event_success`
  - **Behavior**: Insert valid event
  - **Expected**: Event saved with auto-generated ID

- **Test Case**: `test_insert_event_auto_timestamp`
  - **Behavior**: Insert event without timestamp
  - **Expected**: Timestamp auto-generated

- **Test Case**: `test_insert_event_preserve_timestamp`
  - **Behavior**: Insert event with specific timestamp
  - **Expected**: Provided timestamp preserved

- **Test Case**: `test_get_recent_events_empty_db`
  - **Behavior**: Query recent events from empty database
  - **Expected**: Empty list returned

- **Test Case**: `test_get_recent_events_ordering`
  - **Behavior**: Insert events, query recent
  - **Expected**: Events returned in timestamp DESC order

- **Test Case**: `test_get_recent_events_pagination`
  - **Behavior**: Query with limit/offset
  - **Expected**: Correct subset returned

- **Test Case**: `test_get_filter_options_empty_db`
  - **Behavior**: Query filter options from empty database
  - **Expected**: Empty lists for all options

- **Test Case**: `test_get_filter_options_populated`
  - **Behavior**: Insert events, query filter options
  - **Expected**: Unique values for each filter type

- **Test Case**: `test_get_event_count_empty`
  - **Behavior**: Count events in empty database
  - **Expected**: Count = 0

- **Test Case**: `test_get_event_count_populated`
  - **Behavior**: Insert events, count
  - **Expected**: Correct count returned

#### 4.4 Theme Database Tests
- **Test Case**: `test_create_theme_success`
  - **Behavior**: Insert valid theme
  - **Expected**: Theme saved successfully

- **Test Case**: `test_create_theme_duplicate_id`
  - **Behavior**: Insert theme with existing ID
  - **Expected**: Error response with appropriate message

- **Test Case**: `test_get_theme_by_id_exists`
  - **Behavior**: Query existing theme
  - **Expected**: Theme data returned

- **Test Case**: `test_get_theme_by_id_not_found`
  - **Behavior**: Query non-existent theme
  - **Expected**: Error response

- **Test Case**: `test_search_themes_empty_db`
  - **Behavior**: Search themes in empty database
  - **Expected**: Empty results

- **Test Case**: `test_search_themes_text_query`
  - **Behavior**: Search by theme name/description
  - **Expected**: Matching themes returned

- **Test Case**: `test_search_themes_author_filter`
  - **Behavior**: Filter by author ID
  - **Expected**: Only author's themes returned

- **Test Case**: `test_search_themes_public_filter`
  - **Behavior**: Filter by public/private
  - **Expected**: Correct visibility filtering

- **Test Case**: `test_search_themes_sorting`
  - **Behavior**: Sort by different fields (name, created, rating)
  - **Expected**: Correct sort order applied

- **Test Case**: `test_search_themes_pagination`
  - **Behavior**: Search with limit/offset
  - **Expected**: Correct pagination applied

#### 4.5 Database Error Path Tests
- **Test Case**: `test_database_connection_error`
  - **Behavior**: Simulate database connection failure
  - **Expected**: Appropriate error handling

- **Test Case**: `test_database_query_error`
  - **Behavior**: Execute malformed query
  - **Expected**: Error caught and handled

- **Test Case**: `test_database_json_serialization_error`
  - **Behavior**: Store non-serializable data
  - **Expected**: Error handled gracefully

- **Test Case**: `test_database_constraint_violation`
  - **Behavior**: Violate database constraints
  - **Expected**: Constraint error handled

### 5. Negative Paths and Exception Handling

#### 5.1 API Exception Handler Tests
- **Test Case**: `test_validation_exception_handler`
  - **Behavior**: Trigger RequestValidationError
  - **Expected**: Status 400, validation error details

- **Test Case**: `test_pydantic_validation_exception_handler`
  - **Behavior**: Trigger Pydantic ValidationError
  - **Expected**: Status 400, Pydantic error details

- **Test Case**: `test_general_exception_handler`
  - **Behavior**: Trigger unhandled exception
  - **Expected**: Status 500, generic error message

#### 5.2 Event Endpoint Error Tests
- **Test Case**: `test_create_event_database_error`
  - **Behavior**: Database failure during event creation
  - **Expected**: Status 400, error message

- **Test Case**: `test_get_recent_events_database_error`
  - **Behavior**: Database failure during event retrieval
  - **Expected**: Status 500, error message

- **Test Case**: `test_get_filter_options_database_error`
  - **Behavior**: Database failure during filter query
  - **Expected**: Status 500, error message

- **Test Case**: `test_get_event_count_database_error`
  - **Behavior**: Database failure during count query
  - **Expected**: Status 500, error message

#### 5.3 Theme Endpoint Error Tests
- **Test Case**: `test_create_theme_validation_error`
  - **Behavior**: Invalid theme data format
  - **Expected**: Status 400, validation error

- **Test Case**: `test_create_theme_database_error`
  - **Behavior**: Database failure during theme creation
  - **Expected**: Status 400, error response

- **Test Case**: `test_get_theme_database_error`
  - **Behavior**: Database failure during theme retrieval
  - **Expected**: Status 500, error response

- **Test Case**: `test_search_themes_database_error`
  - **Behavior**: Database failure during search
  - **Expected**: Status 500, error response

#### 5.4 WebSocket Error Tests
- **Test Case**: `test_websocket_connection_error`
  - **Behavior**: WebSocket connection failure
  - **Expected**: Connection properly cleaned up

- **Test Case**: `test_websocket_broadcast_error`
  - **Behavior**: Error during message broadcast
  - **Expected**: Failed connections removed

- **Test Case**: `test_websocket_json_serialization_error`
  - **Behavior**: Non-serializable data in broadcast
  - **Expected**: Error handled gracefully

#### 5.5 Configuration Error Tests
- **Test Case**: `test_config_validation_missing_required`
  - **Behavior**: Missing required config in production
  - **Expected**: ValueError with specific message

- **Test Case**: `test_config_invalid_log_level`
  - **Behavior**: Invalid LOG_LEVEL value
  - **Expected**: Default log level used

- **Test Case**: `test_config_invalid_port`
  - **Behavior**: Non-numeric PORT value
  - **Expected**: Validation error

### 6. Branch and Conditional Coverage

#### 6.1 Conditional Logic Tests
- **Test Case**: `test_event_validation_all_branches`
  - **Behavior**: Test all validation conditions in create_event
  - **Expected**: Each branch properly tested

- **Test Case**: `test_websocket_broadcast_conditions`
  - **Behavior**: Test broadcast with/without connections
  - **Expected**: Both empty and populated connection sets

- **Test Case**: `test_theme_search_query_conditions`
  - **Behavior**: Test all search query combinations
  - **Expected**: Each filter condition tested

- **Test Case**: `test_database_json_handling_conditions`
  - **Behavior**: Test JSON serialization/deserialization paths
  - **Expected**: Both success and error conditions

#### 6.2 Error Path Coverage
- **Test Case**: `test_all_exception_paths`
  - **Behavior**: Ensure every try/except block is tested
  - **Expected**: Both success and exception paths covered

- **Test Case**: `test_optional_field_handling`
  - **Behavior**: Test handling of None vs provided optional fields
  - **Expected**: Both None and value conditions tested

## Test Implementation Structure

### Test File Organization
```
tests/
├── conftest.py                 # Test configuration and fixtures
├── test_routes/
│   ├── test_events.py         # Event endpoint tests
│   ├── test_themes.py         # Theme endpoint tests
│   ├── test_websockets.py     # WebSocket tests
│   └── test_health.py         # Health and root endpoint tests
├── test_models/
│   ├── test_hook_event.py     # HookEvent model tests
│   ├── test_theme.py          # Theme model tests
│   └── test_responses.py      # Response model tests
├── test_config/
│   ├── test_settings.py       # Configuration tests
│   └── test_environment.py    # Environment variable tests
├── test_database/
│   ├── test_events_db.py      # Event database tests
│   ├── test_themes_db.py      # Theme database tests
│   └── test_lifecycle.py      # Database lifecycle tests
└── test_error_handling/
    ├── test_exceptions.py     # Exception handler tests
    ├── test_validation.py     # Validation error tests
    └── test_negative_paths.py # Negative path tests
```

### Key Testing Fixtures
```python
@pytest.fixture
def test_client():
    """FastAPI TestClient fixture"""
    
@pytest.fixture
def in_memory_db():
    """In-memory SQLite database fixture"""
    
@pytest.fixture
def sample_event():
    """Sample HookEvent data"""
    
@pytest.fixture
def sample_theme():
    """Sample Theme data"""
    
@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection"""
```

## Coverage Goals
- **Line Coverage**: 100%
- **Branch Coverage**: 100%
- **Function Coverage**: 100%
- **Condition Coverage**: 100%

## Test Execution Strategy
1. **Unit Tests**: Fast, isolated tests for individual components
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Full request/response cycle testing
4. **Error Simulation**: Mock failures and edge cases
5. **Performance Tests**: Ensure tests complete within reasonable time

This comprehensive test plan ensures every behavior, branch, and conditional in the FastAPI application is explicitly tested with appropriate assertions and error handling verification.
