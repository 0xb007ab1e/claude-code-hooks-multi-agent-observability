package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
)

// Config represents the server configuration
type Config struct {
	Port                   int
	Host                   string
	DatabasePath           string
	CorsOrigins            string
	PostgresURL            string
	DatabaseURL            string
	DBPassword             string
	DBHost                 string
	DBPort                 int
	DBName                 string
	DBUser                 string
	APIKey                 string
	JWTSecret              string
	RateLimitWindowMS      int
	RateLimitMaxRequests   int
	WSHeartbeatInterval    int
	LogLevel               string
	Environment            string
}

// DefaultConfig returns default configuration values
func DefaultConfig() *Config {
	return &Config{
		Port:                   8092, // Go server port
		Host:                   "0.0.0.0",
		DatabasePath:           "events.db",
		CorsOrigins:            "*",
		RateLimitWindowMS:      900000, // 15 minutes
		RateLimitMaxRequests:   100,
		WSHeartbeatInterval:    30000, // 30 seconds
		LogLevel:               "info",
		Environment:            "development",
	}
}

// LoadConfig loads configuration from environment variables
func LoadConfig() (*Config, error) {
	// Load .env file if it exists
	godotenv.Load()

	cfg := DefaultConfig()

	// Override with environment variables
	if port := os.Getenv("PORT"); port != "" {
		if p, err := strconv.Atoi(port); err == nil {
			cfg.Port = p
		}
	}

	if host := os.Getenv("HOST"); host != "" {
		cfg.Host = host
	}

	if dbPath := os.Getenv("DATABASE_PATH"); dbPath != "" {
		cfg.DatabasePath = dbPath
	}

	if cors := os.Getenv("CORS_ORIGINS"); cors != "" {
		cfg.CorsOrigins = cors
	}

	if postgresURL := os.Getenv("POSTGRES_URL"); postgresURL != "" {
		cfg.PostgresURL = postgresURL
	}

	if databaseURL := os.Getenv("DATABASE_URL"); databaseURL != "" {
		cfg.DatabaseURL = databaseURL
	}

	if dbPassword := os.Getenv("DB_PASSWORD"); dbPassword != "" {
		cfg.DBPassword = dbPassword
	}

	if dbHost := os.Getenv("DB_HOST"); dbHost != "" {
		cfg.DBHost = dbHost
	}

	if dbPort := os.Getenv("DB_PORT"); dbPort != "" {
		if p, err := strconv.Atoi(dbPort); err == nil {
			cfg.DBPort = p
		}
	}

	if dbName := os.Getenv("DB_NAME"); dbName != "" {
		cfg.DBName = dbName
	}

	if dbUser := os.Getenv("DB_USER"); dbUser != "" {
		cfg.DBUser = dbUser
	}

	if apiKey := os.Getenv("API_KEY"); apiKey != "" {
		cfg.APIKey = apiKey
	}

	if jwtSecret := os.Getenv("JWT_SECRET"); jwtSecret != "" {
		cfg.JWTSecret = jwtSecret
	}

	if rateLimitWindow := os.Getenv("RATE_LIMIT_WINDOW_MS"); rateLimitWindow != "" {
		if rlw, err := strconv.Atoi(rateLimitWindow); err == nil {
			cfg.RateLimitWindowMS = rlw
		}
	}

	if rateLimitMax := os.Getenv("RATE_LIMIT_MAX_REQUESTS"); rateLimitMax != "" {
		if rlm, err := strconv.Atoi(rateLimitMax); err == nil {
			cfg.RateLimitMaxRequests = rlm
		}
	}

	if wsHeartbeat := os.Getenv("WS_HEARTBEAT_INTERVAL"); wsHeartbeat != "" {
		if wsh, err := strconv.Atoi(wsHeartbeat); err == nil {
			cfg.WSHeartbeatInterval = wsh
		}
	}

	if logLevel := os.Getenv("LOG_LEVEL"); logLevel != "" {
		cfg.LogLevel = logLevel
	}

	if environment := os.Getenv("ENVIRONMENT"); environment != "" {
		cfg.Environment = environment
	}

	// Validate required configuration
	if err := cfg.Validate(); err != nil {
		return nil, err
	}

	return cfg, nil
}

// Validate validates the configuration
func (c *Config) Validate() error {
	if c.Environment == "production" {
		if c.DatabasePath == "" {
			return fmt.Errorf("DATABASE_PATH is required in production")
		}
	}

	return nil
}

// GetCorsOrigins returns CORS origins as a slice
func (c *Config) GetCorsOrigins() []string {
	if c.CorsOrigins == "*" {
		return []string{"*"}
	}
	return strings.Split(c.CorsOrigins, ",")
}

// PrintConfig prints the configuration (for debugging)
func (c *Config) PrintConfig() {
	fmt.Printf("✅ Go server configuration loaded\n")
	fmt.Printf("📦 Environment: %s\n", c.Environment)
	fmt.Printf("🚀 Server will run on port: %d\n", c.Port)
	fmt.Printf("💾 Database path: %s\n", c.DatabasePath)
	fmt.Printf("🌐 CORS origins: %s\n", c.CorsOrigins)
}
