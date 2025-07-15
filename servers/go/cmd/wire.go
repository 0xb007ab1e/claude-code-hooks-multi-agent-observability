//+build wireinject

package main

import (
	"github.com/google/wire"

	"multi-agent-observability-server-go/internal/config"
	"multi-agent-observability-server-go/internal/database"
	"multi-agent-observability-server-go/internal/handlers"
	"multi-agent-observability-server-go/internal/services"
	"multi-agent-observability-server-go/internal/websocket"
)

func InitializeServer() (*handlers.Server, error) {
	wire.Build(
		config.LoadConfig,
		database.NewDatabase,
		services.NewServiceContainer,
		websocket.NewWebSocketManager,
		handlers.NewServer,
	)
	return nil, nil
}
