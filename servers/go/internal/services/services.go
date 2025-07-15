package services

import (
	"fmt"
	"sync"

	"multi-agent-observability-server-go/internal/database"
	"multi-agent-observability-server-go/pkg/models"
)

// EventService handles event-related operations
type EventService struct {
	db database.DatabaseInterface
}

// EventServiceInterface defines the event service operations
type EventServiceInterface interface {
	CreateEvent(event *models.HookEvent) (*models.HookEvent, error)
	GetRecentEvents(limit, offset int) ([]*models.HookEvent, error)
	GetFilterOptions() (*models.FilterOptions, error)
	GetEventCount() (int64, error)
}

// NewEventService creates a new event service
func NewEventService(db database.DatabaseInterface) *EventService {
	return &EventService{db: db}
}

// CreateEvent creates a new event with validation
func (s *EventService) CreateEvent(event *models.HookEvent) (*models.HookEvent, error) {
	if !event.IsValid() {
		return nil, fmt.Errorf("missing required fields")
	}
	return s.db.InsertEvent(event)
}

// GetRecentEvents retrieves recent events with pagination
func (s *EventService) GetRecentEvents(limit, offset int) ([]*models.HookEvent, error) {
	return s.db.GetRecentEvents(limit, offset)
}

// GetFilterOptions retrieves available filter options
func (s *EventService) GetFilterOptions() (*models.FilterOptions, error) {
	return s.db.GetFilterOptions()
}

// GetEventCount retrieves the total event count
func (s *EventService) GetEventCount() (int64, error) {
	return s.db.GetEventCount()
}

// ThemeService handles theme-related operations
type ThemeService struct {
	db database.DatabaseInterface
}

// ThemeServiceInterface defines the theme service operations
type ThemeServiceInterface interface {
	CreateTheme(theme *models.Theme) (*models.ApiResponse, error)
	GetThemeByID(themeID string) (*models.ApiResponse, error)
	SearchThemes(query *models.ThemeSearchQuery) (*models.ApiResponse, error)
	GetThemeStats() (map[string]interface{}, error)
}

// NewThemeService creates a new theme service
func NewThemeService(db database.DatabaseInterface) *ThemeService {
	return &ThemeService{db: db}
}

// CreateTheme creates a new theme
func (s *ThemeService) CreateTheme(theme *models.Theme) (*models.ApiResponse, error) {
	if valid, errors := theme.IsValid(); !valid {
		return &models.ApiResponse{
			Success:          false,
			ValidationErrors: errors,
		}, nil
	}
	return s.db.CreateTheme(theme)
}

// GetThemeByID retrieves a theme by its ID
func (s *ThemeService) GetThemeByID(themeID string) (*models.ApiResponse, error) {
	if themeID == "" {
		errorMsg := "Theme ID is required"
		return &models.ApiResponse{
			Success: false,
			Error:   &errorMsg,
		}, nil
	}
	return s.db.GetThemeByID(themeID)
}

// SearchThemes searches for themes based on query parameters
func (s *ThemeService) SearchThemes(query *models.ThemeSearchQuery) (*models.ApiResponse, error) {
	return s.db.SearchThemes(query)
}

// GetThemeStats retrieves theme statistics
func (s *ThemeService) GetThemeStats() (map[string]interface{}, error) {
	// Placeholder implementation
	return map[string]interface{}{
		"total":   0,
		"public":  0,
		"private": 0,
	}, nil
}

// WebSocketService handles WebSocket connections and broadcasting
type WebSocketService struct {
	connections map[*WebSocketConnection]bool
	mu          sync.RWMutex
}

// WebSocketConnection represents a WebSocket connection
type WebSocketConnection struct {
	ID   string
	Conn interface{} // Will be *websocket.Conn in actual implementation
}

// WebSocketServiceInterface defines the WebSocket service operations
type WebSocketServiceInterface interface {
	AddConnection(conn *WebSocketConnection)
	RemoveConnection(conn *WebSocketConnection)
	BroadcastMessage(message *models.WebSocketMessage) error
	SendInitialData(conn *WebSocketConnection, eventService EventServiceInterface) error
}

// NewWebSocketService creates a new WebSocket service
func NewWebSocketService() *WebSocketService {
	return &WebSocketService{
		connections: make(map[*WebSocketConnection]bool),
	}
}

// AddConnection adds a new WebSocket connection
func (s *WebSocketService) AddConnection(conn *WebSocketConnection) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.connections[conn] = true
}

// RemoveConnection removes a WebSocket connection
func (s *WebSocketService) RemoveConnection(conn *WebSocketConnection) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.connections, conn)
}

// BroadcastMessage broadcasts a message to all connected clients
func (s *WebSocketService) BroadcastMessage(message *models.WebSocketMessage) error {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if len(s.connections) == 0 {
		return nil
	}

	// Create a copy of connections to avoid modification during iteration
	connectionsCopy := make([]*WebSocketConnection, 0, len(s.connections))
	for conn := range s.connections {
		connectionsCopy = append(connectionsCopy, conn)
	}

	for _, conn := range connectionsCopy {
		// In actual implementation, this would send the message to the WebSocket
		// For now, we'll just log or handle it as needed
		_ = conn // Use the connection to send the message
	}

	return nil
}

// SendInitialData sends initial data to a new WebSocket connection
func (s *WebSocketService) SendInitialData(conn *WebSocketConnection, eventService EventServiceInterface) error {
	recentEvents, err := eventService.GetRecentEvents(50, 0)
	if err != nil {
		return fmt.Errorf("failed to get recent events: %w", err)
	}

	message := &models.WebSocketMessage{
		Type: "initial",
		Data: recentEvents,
	}

	// In actual implementation, this would send the message to the specific connection
	_ = message
	_ = conn

	return nil
}

// NotificationService handles event notifications
type NotificationService struct {
	websocketService WebSocketServiceInterface
}

// NotificationServiceInterface defines the notification service operations
type NotificationServiceInterface interface {
	NotifyEventCreated(event *models.HookEvent) error
}

// NewNotificationService creates a new notification service
func NewNotificationService(wsService WebSocketServiceInterface) *NotificationService {
	return &NotificationService{
		websocketService: wsService,
	}
}

// NotifyEventCreated notifies all clients about a new event
func (s *NotificationService) NotifyEventCreated(event *models.HookEvent) error {
	message := &models.WebSocketMessage{
		Type: "event",
		Data: event,
	}

	return s.websocketService.BroadcastMessage(message)
}

// ServiceContainer holds all services for dependency injection
type ServiceContainer struct {
	EventService        EventServiceInterface
	ThemeService        ThemeServiceInterface
	WebSocketService    WebSocketServiceInterface
	NotificationService NotificationServiceInterface
}

// NewServiceContainer creates a new service container
func NewServiceContainer(db database.DatabaseInterface) *ServiceContainer {
	eventService := NewEventService(db)
	themeService := NewThemeService(db)
	websocketService := NewWebSocketService()
	notificationService := NewNotificationService(websocketService)

	return &ServiceContainer{
		EventService:        eventService,
		ThemeService:        themeService,
		WebSocketService:    websocketService,
		NotificationService: notificationService,
	}
}
