package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"multi-agent-observability-server-go/internal/config"
	"multi-agent-observability-server-go/internal/database"
	"multi-agent-observability-server-go/internal/handlers"
	"multi-agent-observability-server-go/internal/services"
	"multi-agent-observability-server-go/internal/websocket"

	"github.com/sirupsen/logrus"
)

func main() {
	// Load configuration
	cfg, err := config.LoadConfig()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Setup logging
	logLevel, err := logrus.ParseLevel(cfg.LogLevel)
	if err != nil {
		logLevel = logrus.InfoLevel
	}
	logrus.SetLevel(logLevel)
	logrus.SetFormatter(&logrus.JSONFormatter{})

	// Initialize database
	db, err := database.NewDatabase(cfg.DatabasePath)
	if err != nil {
		logrus.Fatalf("Failed to initialize database: %v", err)
	}
	defer db.Close()

	// Initialize services
	serviceContainer := services.NewServiceContainer(db)

	// Initialize WebSocket manager
	wsManager := websocket.NewWebSocketManager()

	// Initialize server
	server := handlers.NewServer(cfg, serviceContainer, wsManager)

	// Setup HTTP server
	httpServer := &http.Server{
		Addr:    fmt.Sprintf("%s:%d", cfg.Host, cfg.Port),
		Handler: server.SetupRoutes(),
	}

	// Start server in a goroutine
	go func() {
		logrus.Infof("🚀 Go server starting on %s:%d", cfg.Host, cfg.Port)
		logrus.Infof("📦 Environment: %s", cfg.Environment)
		logrus.Infof("💾 Database: %s", cfg.DatabasePath)
		logrus.Info("🔌 WebSocket server ready")

		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logrus.Fatalf("Failed to start server: %v", err)
		}
	}()

	// Wait for interrupt signal to gracefully shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logrus.Info("Server shutting down...")

	// Give the server 30 seconds to shutdown gracefully
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := httpServer.Shutdown(ctx); err != nil {
		logrus.Fatalf("Server forced to shutdown: %v", err)
	}

	logrus.Info("Server exited")
}
