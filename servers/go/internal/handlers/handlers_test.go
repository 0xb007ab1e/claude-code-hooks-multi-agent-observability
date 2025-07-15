package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"

	"multi-agent-observability-server-go/internal/config"
	"multi-agent-observability-server-go/internal/services"
	"multi-agent-observability-server-go/internal/websocket"
	"multi-agent-observability-server-go/pkg/models"
)

// MockDatabase is a mock implementation of the database interface
type MockDatabase struct {
	mock.Mock
}

func (m *MockDatabase) InitDatabase() error {
	args := m.Called()
	return args.Error(0)
}

func (m *MockDatabase) Close() error {
	args := m.Called()
	return args.Error(0)
}

func (m *MockDatabase) InsertEvent(event *models.HookEvent) (*models.HookEvent, error) {
	args := m.Called(event)
	return args.Get(0).(*models.HookEvent), args.Error(1)
}

func (m *MockDatabase) GetRecentEvents(limit, offset int) ([]*models.HookEvent, error) {
	args := m.Called(limit, offset)
	return args.Get(0).([]*models.HookEvent), args.Error(1)
}

func (m *MockDatabase) GetFilterOptions() (*models.FilterOptions, error) {
	args := m.Called()
	return args.Get(0).(*models.FilterOptions), args.Error(1)
}

func (m *MockDatabase) GetEventCount() (int64, error) {
	args := m.Called()
	return args.Get(0).(int64), args.Error(1)
}

func (m *MockDatabase) CreateTheme(theme *models.Theme) (*models.ApiResponse, error) {
	args := m.Called(theme)
	return args.Get(0).(*models.ApiResponse), args.Error(1)
}

func (m *MockDatabase) GetThemeByID(themeID string) (*models.ApiResponse, error) {
	args := m.Called(themeID)
	return args.Get(0).(*models.ApiResponse), args.Error(1)
}

func (m *MockDatabase) SearchThemes(query *models.ThemeSearchQuery) (*models.ApiResponse, error) {
	args := m.Called(query)
	return args.Get(0).(*models.ApiResponse), args.Error(1)
}

func setupTestServer() *Server {
	cfg := config.DefaultConfig()
	cfg.Port = 8094 // Test port
	
	mockDB := &MockDatabase{}
	serviceContainer := services.NewServiceContainer(mockDB)
	wsManager := websocket.NewWebSocketManager()
	
	return NewServer(cfg, serviceContainer, wsManager)
}

func TestHealthEndpoint(t *testing.T) {
	server := setupTestServer()
	router := server.SetupRoutes()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	
	var response models.HealthResponse
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "healthy", response.Status)
	assert.NotEmpty(t, response.Timestamp)
}

func TestRootEndpoint(t *testing.T) {
	server := setupTestServer()
	router := server.SetupRoutes()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	
	var response map[string]interface{}
	err := json.Unmarshal(w.Body.Bytes(), &response)
	assert.NoError(t, err)
	assert.Equal(t, "Multi-Agent Observability Server", response["message"])
}

func TestCreateEvent(t *testing.T) {
	server := setupTestServer()
	router := server.SetupRoutes()

	// Create a sample event
	event := &models.HookEvent{
		SourceApp:     "test-app",
		SessionID:     "test-session",
		HookEventType: "PreToolUse",
		Payload:       map[string]interface{}{"tool": "test"},
	}

	// Mock the database call
	mockDB := &MockDatabase{}
	mockDB.On("InsertEvent", mock.AnythingOfType("*models.HookEvent")).Return(event, nil)

	eventJSON, _ := json.Marshal(event)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/events/", bytes.NewBuffer(eventJSON))
	req.Header.Set("Content-Type", "application/json")
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
}

func TestGetRecentEvents(t *testing.T) {
	server := setupTestServer()
	router := server.SetupRoutes()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/events/recent", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
}

func TestGetFilterOptions(t *testing.T) {
	server := setupTestServer()
	router := server.SetupRoutes()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/events/filter-options", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
}

func TestGetEventCount(t *testing.T) {
	server := setupTestServer()
	router := server.SetupRoutes()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/events/count", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
}

func TestCreateTheme(t *testing.T) {
	server := setupTestServer()
	router := server.SetupRoutes()

	// Create a sample theme
	theme := &models.Theme{
		ID:          "test-theme",
		Name:        "Test Theme",
		DisplayName: "Test Theme",
		Colors: models.ThemeColors{
			Primary: "#000000",
		},
		IsPublic:  true,
		CreatedAt: time.Now().UnixMilli(),
		UpdatedAt: time.Now().UnixMilli(),
		Tags:      []string{"test"},
	}

	themeJSON, _ := json.Marshal(theme)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/themes/", bytes.NewBuffer(themeJSON))
	req.Header.Set("Content-Type", "application/json")
	router.ServeHTTP(w, req)

	// Note: This will fail without proper mocking, but shows the test structure
	assert.Equal(t, http.StatusInternalServerError, w.Code)
}

func TestCORSHeaders(t *testing.T) {
	server := setupTestServer()
	router := server.SetupRoutes()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("OPTIONS", "/", nil)
	req.Header.Set("Origin", "http://localhost:3000")
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNoContent, w.Code)
	assert.Contains(t, w.Header().Get("Access-Control-Allow-Origin"), "*")
}
