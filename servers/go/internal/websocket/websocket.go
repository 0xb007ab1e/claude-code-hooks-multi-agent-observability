package websocket

import (
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/sirupsen/logrus"

	"multi-agent-observability-server-go/internal/services"
	"multi-agent-observability-server-go/pkg/models"
)

// WebSocketManager manages WebSocket connections
type WebSocketManager struct {
	upgrader    websocket.Upgrader
	clients     map[*websocket.Conn]bool
	broadcast   chan models.WebSocketMessage
	register    chan *websocket.Conn
	unregister  chan *websocket.Conn
	mu          sync.RWMutex
}

// NewWebSocketManager creates a new WebSocket manager
func NewWebSocketManager() *WebSocketManager {
	return &WebSocketManager{
		upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool {
				return true // Allow all origins for now
			},
		},
		clients:    make(map[*websocket.Conn]bool),
		broadcast:  make(chan models.WebSocketMessage),
		register:   make(chan *websocket.Conn),
		unregister: make(chan *websocket.Conn),
	}
}

// Start starts the WebSocket manager
func (m *WebSocketManager) Start() {
	go m.run()
}

// run handles WebSocket connections
func (m *WebSocketManager) run() {
	for {
		select {
		case client := <-m.register:
			m.mu.Lock()
			m.clients[client] = true
			m.mu.Unlock()
			logrus.Info("New WebSocket client connected")

		case client := <-m.unregister:
			m.mu.Lock()
			if _, ok := m.clients[client]; ok {
				delete(m.clients, client)
				client.Close()
			}
			m.mu.Unlock()
			logrus.Info("WebSocket client disconnected")

		case message := <-m.broadcast:
			m.mu.RLock()
			for client := range m.clients {
				if err := client.WriteJSON(message); err != nil {
					logrus.WithError(err).Error("Failed to write to WebSocket client")
					client.Close()
					delete(m.clients, client)
				}
			}
			m.mu.RUnlock()
		}
	}
}

// HandleConnection handles a new WebSocket connection
func (m *WebSocketManager) HandleConnection(w http.ResponseWriter, r *http.Request, services *services.ServiceContainer) error {
	conn, err := m.upgrader.Upgrade(w, r, nil)
	if err != nil {
		return err
	}

	m.register <- conn

	// Set up ping/pong handlers
	conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	conn.SetPongHandler(func(string) error {
		conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	go m.handleClient(conn)

	return nil
}

// handleClient handles individual client connections
func (m *WebSocketManager) handleClient(conn *websocket.Conn) {
	defer func() {
		m.unregister <- conn
		conn.Close()
	}()

	for {
		// Read message from client
		_, _, err := conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				logrus.WithError(err).Error("WebSocket error")
			}
			break
		}

		// Handle ping/pong
		ticker := time.NewTicker(54 * time.Second)
		defer ticker.Stop()

		select {
		case <-ticker.C:
			conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// BroadcastMessage broadcasts a message to all connected clients
func (m *WebSocketManager) BroadcastMessage(message models.WebSocketMessage) {
	select {
	case m.broadcast <- message:
	default:
		logrus.Warn("WebSocket broadcast channel full")
	}
}

// GetClientCount returns the number of connected clients
func (m *WebSocketManager) GetClientCount() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return len(m.clients)
}
