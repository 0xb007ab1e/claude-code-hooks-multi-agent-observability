package handlers

import (
	"net/http"
	"strconv"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"

	"multi-agent-observability-server-go/internal/config"
	"multi-agent-observability-server-go/internal/services"
	"multi-agent-observability-server-go/internal/websocket"
	"multi-agent-observability-server-go/pkg/models"
)

// Server represents the HTTP server with all dependencies
type Server struct {
	config    *config.Config
	services  *services.ServiceContainer
	wsManager *websocket.WebSocketManager
}

// NewServer creates a new server instance
func NewServer(config *config.Config, services *services.ServiceContainer, wsManager *websocket.WebSocketManager) *Server {
	return &Server{
		config:    config,
		services:  services,
		wsManager: wsManager,
	}
}

// SetupRoutes configures all the routes for the server
func (s *Server) SetupRoutes() *gin.Engine {
	// Set Gin mode based on environment
	if s.config.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	} else {
		gin.SetMode(gin.DebugMode)
	}

	router := gin.New()

	// Add middleware
	router.Use(gin.Logger())
	router.Use(gin.Recovery())

	// CORS middleware
	router.Use(cors.New(cors.Config{
		AllowOrigins:     s.config.GetCorsOrigins(),
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Content-Length", "Accept-Encoding", "X-CSRF-Token", "Authorization"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	// Routes
	s.setupHealthRoutes(router)
	s.setupEventRoutes(router)
	s.setupThemeRoutes(router)
	s.setupWebSocketRoutes(router)

	return router
}

// setupHealthRoutes sets up health check routes
func (s *Server) setupHealthRoutes(router *gin.Engine) {
	// Root endpoint
	router.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "Multi-Agent Observability Server",
		})
	})

	// Health check endpoint
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, models.HealthResponse{
			Status:    "healthy",
			Timestamp: time.Now().Format(time.RFC3339),
		})
	})
}

// setupEventRoutes sets up event-related routes
func (s *Server) setupEventRoutes(router *gin.Engine) {
	events := router.Group("/events")
	{
		events.POST("/", s.createEvent)
		events.GET("/recent", s.getRecentEvents)
		events.GET("/filter-options", s.getFilterOptions)
		events.GET("/count", s.getEventCount)
	}
}

// setupThemeRoutes sets up theme-related routes
func (s *Server) setupThemeRoutes(router *gin.Engine) {
	themes := router.Group("/api/themes")
	{
		themes.POST("/", s.createTheme)
		themes.GET("/stats", s.getThemeStats)
		themes.GET("/", s.searchThemes)
		themes.GET("/:id", s.getThemeByID)
	}
}

// setupWebSocketRoutes sets up WebSocket routes
func (s *Server) setupWebSocketRoutes(router *gin.Engine) {
	router.GET("/stream", s.handleWebSocket)
}

// Event Handlers

// createEvent creates a new event
func (s *Server) createEvent(c *gin.Context) {
	var event models.HookEvent
	if err := c.ShouldBindJSON(&event); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	createdEvent, err := s.services.EventService.CreateEvent(&event)
	if err != nil {
		logrus.WithError(err).Error("Failed to create event")
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Notify WebSocket clients
	if err := s.services.NotificationService.NotifyEventCreated(createdEvent); err != nil {
		logrus.WithError(err).Warn("Failed to notify WebSocket clients")
	}

	c.JSON(http.StatusOK, createdEvent)
}

// getRecentEvents retrieves recent events
func (s *Server) getRecentEvents(c *gin.Context) {
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	offset, _ := strconv.Atoi(c.DefaultQuery("offset", "0"))

	events, err := s.services.EventService.GetRecentEvents(limit, offset)
	if err != nil {
		logrus.WithError(err).Error("Failed to get recent events")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, events)
}

// getFilterOptions retrieves available filter options
func (s *Server) getFilterOptions(c *gin.Context) {
	options, err := s.services.EventService.GetFilterOptions()
	if err != nil {
		logrus.WithError(err).Error("Failed to get filter options")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, options)
}

// getEventCount retrieves the total event count
func (s *Server) getEventCount(c *gin.Context) {
	count, err := s.services.EventService.GetEventCount()
	if err != nil {
		logrus.WithError(err).Error("Failed to get event count")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, models.EventCount{Count: count})
}

// Theme Handlers

// createTheme creates a new theme
func (s *Server) createTheme(c *gin.Context) {
	var theme models.Theme
	if err := c.ShouldBindJSON(&theme); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	response, err := s.services.ThemeService.CreateTheme(&theme)
	if err != nil {
		logrus.WithError(err).Error("Failed to create theme")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	if response.Success {
		c.JSON(http.StatusCreated, response.Data)
	} else {
		c.JSON(http.StatusBadRequest, response)
	}
}

// getThemeStats retrieves theme statistics
func (s *Server) getThemeStats(c *gin.Context) {
	stats, err := s.services.ThemeService.GetThemeStats()
	if err != nil {
		logrus.WithError(err).Error("Failed to get theme stats")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":    stats,
	})
}

// searchThemes searches for themes
func (s *Server) searchThemes(c *gin.Context) {
	var query models.ThemeSearchQuery
	if err := c.ShouldBindQuery(&query); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid query parameters"})
		return
	}

	response, err := s.services.ThemeService.SearchThemes(&query)
	if err != nil {
		logrus.WithError(err).Error("Failed to search themes")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	if response.Success {
		c.JSON(http.StatusOK, gin.H{
			"success": true,
			"themes":  response.Data,
		})
	} else {
		c.JSON(http.StatusBadRequest, response)
	}
}

// getThemeByID retrieves a theme by its ID
func (s *Server) getThemeByID(c *gin.Context) {
	themeID := c.Param("id")
	if themeID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Theme ID is required"})
		return
	}

	response, err := s.services.ThemeService.GetThemeByID(themeID)
	if err != nil {
		logrus.WithError(err).Error("Failed to get theme by ID")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal server error"})
		return
	}

	if response.Success {
		c.JSON(http.StatusOK, response.Data)
	} else {
		c.JSON(http.StatusNotFound, response)
	}
}

// handleWebSocket handles WebSocket connections
func (s *Server) handleWebSocket(c *gin.Context) {
	if err := s.wsManager.HandleConnection(c.Writer, c.Request, s.services); err != nil {
		logrus.WithError(err).Error("Failed to handle WebSocket connection")
		c.JSON(http.StatusInternalServerError, gin.H{"error": "WebSocket connection failed"})
		return
	}
}
