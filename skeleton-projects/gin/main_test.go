package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func setupRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	r := gin.Default()

	r.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, MessageResponse{
			Message: "Gin skeleton API is running!",
		})
	})

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, HealthResponse{
			Status:    "healthy",
			Timestamp: "2023-01-01T00:00:00Z",
		})
	})

	r.GET("/api/users", getUsers)
	r.POST("/api/users", createUser)
	r.GET("/api/users/:id", getUser)

	return r
}

func TestMain(m *testing.M) {
	// Reset users for each test
	users = []User{}
	userIDCounter = 1
	m.Run()
}

func TestGetRoot(t *testing.T) {
	router := setupRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	
	var response MessageResponse
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(t, "Gin skeleton API is running!", response.Message)
}

func TestGetHealth(t *testing.T) {
	router := setupRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	
	var response HealthResponse
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(t, "healthy", response.Status)
	assert.NotEmpty(t, response.Timestamp)
}

func TestGetUsersEmpty(t *testing.T) {
	router := setupRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/users", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	
	var response map[string][]User
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(t, 0, len(response["users"]))
}

func TestCreateUser(t *testing.T) {
	router := setupRouter()
	
	user := User{
		Name:  "John Doe",
		Email: "john@example.com",
	}
	jsonData, _ := json.Marshal(user)
	
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/users", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)
	
	var response User
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(t, "John Doe", response.Name)
	assert.Equal(t, "john@example.com", response.Email)
	assert.Equal(t, 1, response.ID)
}

func TestGetUser(t *testing.T) {
	router := setupRouter()
	
	// First create a user
	user := User{
		Name:  "Jane Doe",
		Email: "jane@example.com",
	}
	jsonData, _ := json.Marshal(user)
	
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/users", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	router.ServeHTTP(w, req)
	
	// Then get the user
	w = httptest.NewRecorder()
	req, _ = http.NewRequest("GET", "/api/users/1", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	
	var response User
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(t, "Jane Doe", response.Name)
	assert.Equal(t, "jane@example.com", response.Email)
	assert.Equal(t, 1, response.ID)
}

func TestGetNonexistentUser(t *testing.T) {
	router := setupRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/users/999", nil)
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusNotFound, w.Code)
	
	var response map[string]string
	json.Unmarshal(w.Body.Bytes(), &response)
	assert.Equal(t, "User not found", response["error"])
}
