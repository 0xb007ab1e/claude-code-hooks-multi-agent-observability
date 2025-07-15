package models

import (
	"encoding/json"
	"time"
)

// HookEvent represents an event in the system
type HookEvent struct {
	ID            *int64                 `json:"id,omitempty" db:"id"`
	SourceApp     string                 `json:"source_app" db:"source_app"`
	SessionID     string                 `json:"session_id" db:"session_id"`
	HookEventType string                 `json:"hook_event_type" db:"hook_event_type"`
	Payload       map[string]interface{} `json:"payload" db:"payload"`
	Chat          []interface{}          `json:"chat,omitempty" db:"chat"`
	Summary       *string                `json:"summary,omitempty" db:"summary"`
	Timestamp     *int64                 `json:"timestamp,omitempty" db:"timestamp"`
}

// FilterOptions represents available filter options
type FilterOptions struct {
	SourceApps      []string `json:"source_apps"`
	SessionIDs      []string `json:"session_ids"`
	HookEventTypes  []string `json:"hook_event_types"`
}

// ThemeColors represents theme color configuration
type ThemeColors struct {
	Primary         string `json:"primary"`
	PrimaryHover    string `json:"primaryHover"`
	PrimaryLight    string `json:"primaryLight"`
	PrimaryDark     string `json:"primaryDark"`
	BgPrimary       string `json:"bgPrimary"`
	BgSecondary     string `json:"bgSecondary"`
	BgTertiary      string `json:"bgTertiary"`
	BgQuaternary    string `json:"bgQuaternary"`
	TextPrimary     string `json:"textPrimary"`
	TextSecondary   string `json:"textSecondary"`
	TextTertiary    string `json:"textTertiary"`
	TextQuaternary  string `json:"textQuaternary"`
	BorderPrimary   string `json:"borderPrimary"`
	BorderSecondary string `json:"borderSecondary"`
	BorderTertiary  string `json:"borderTertiary"`
	AccentSuccess   string `json:"accentSuccess"`
	AccentWarning   string `json:"accentWarning"`
	AccentError     string `json:"accentError"`
	AccentInfo      string `json:"accentInfo"`
	Shadow          string `json:"shadow"`
	ShadowLg        string `json:"shadowLg"`
	HoverBg         string `json:"hoverBg"`
	ActiveBg        string `json:"activeBg"`
	FocusRing       string `json:"focusRing"`
}

// Theme represents a theme configuration
type Theme struct {
	ID            string       `json:"id" db:"id"`
	Name          string       `json:"name" db:"name"`
	DisplayName   string       `json:"displayName" db:"displayName"`
	Description   *string      `json:"description,omitempty" db:"description"`
	Colors        ThemeColors  `json:"colors" db:"colors"`
	IsPublic      bool         `json:"isPublic" db:"isPublic"`
	AuthorID      *string      `json:"authorId,omitempty" db:"authorId"`
	AuthorName    *string      `json:"authorName,omitempty" db:"authorName"`
	CreatedAt     int64        `json:"createdAt" db:"createdAt"`
	UpdatedAt     int64        `json:"updatedAt" db:"updatedAt"`
	Tags          []string     `json:"tags" db:"tags"`
	DownloadCount *int         `json:"downloadCount,omitempty" db:"downloadCount"`
	Rating        *float64     `json:"rating,omitempty" db:"rating"`
	RatingCount   *int         `json:"ratingCount,omitempty" db:"ratingCount"`
}

// ThemeSearchQuery represents search parameters for themes
type ThemeSearchQuery struct {
	Query     *string  `json:"query,omitempty" form:"query"`
	Tags      []string `json:"tags,omitempty" form:"tags"`
	AuthorID  *string  `json:"authorId,omitempty" form:"authorId"`
	IsPublic  *bool    `json:"isPublic,omitempty" form:"isPublic"`
	SortBy    *string  `json:"sortBy,omitempty" form:"sortBy"`
	SortOrder *string  `json:"sortOrder,omitempty" form:"sortOrder"`
	Limit     *int     `json:"limit,omitempty" form:"limit"`
	Offset    *int     `json:"offset,omitempty" form:"offset"`
}

// ApiResponse represents a generic API response
type ApiResponse struct {
	Success           bool                   `json:"success"`
	Data              interface{}            `json:"data,omitempty"`
	Error             *string                `json:"error,omitempty"`
	Message           *string                `json:"message,omitempty"`
	ValidationErrors  []ValidationError      `json:"validationErrors,omitempty"`
}

// ValidationError represents a validation error
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
	Code    string `json:"code"`
}

// EventCount represents the count of events
type EventCount struct {
	Count int64 `json:"count"`
}

// HealthResponse represents a health check response
type HealthResponse struct {
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
}

// WebSocketMessage represents a WebSocket message
type WebSocketMessage struct {
	Type string      `json:"type"`
	Data interface{} `json:"data"`
}

// Validation methods
func (h *HookEvent) IsValid() bool {
	return h.SourceApp != "" && h.SessionID != "" && h.HookEventType != "" && h.Payload != nil
}

func (t *Theme) IsValid() (bool, []ValidationError) {
	var errors []ValidationError

	if t.ID == "" {
		errors = append(errors, ValidationError{Field: "id", Message: "ID is required", Code: "required"})
	}
	if t.Name == "" {
		errors = append(errors, ValidationError{Field: "name", Message: "Name is required", Code: "required"})
	}
	if t.DisplayName == "" {
		errors = append(errors, ValidationError{Field: "displayName", Message: "Display name is required", Code: "required"})
	}
	if t.CreatedAt == 0 {
		errors = append(errors, ValidationError{Field: "createdAt", Message: "CreatedAt is required", Code: "required"})
	}
	if t.UpdatedAt == 0 {
		errors = append(errors, ValidationError{Field: "updatedAt", Message: "UpdatedAt is required", Code: "required"})
	}
	if t.Tags == nil {
		errors = append(errors, ValidationError{Field: "tags", Message: "Tags must be an array", Code: "required"})
	}

	return len(errors) == 0, errors
}

// Helper methods for database serialization
func (h *HookEvent) PayloadJSON() ([]byte, error) {
	return json.Marshal(h.Payload)
}

func (h *HookEvent) ChatJSON() ([]byte, error) {
	if h.Chat == nil {
		return nil, nil
	}
	return json.Marshal(h.Chat)
}

func (t *Theme) ColorsJSON() ([]byte, error) {
	return json.Marshal(t.Colors)
}

func (t *Theme) TagsJSON() ([]byte, error) {
	return json.Marshal(t.Tags)
}

// Helper methods for setting timestamps
func (h *HookEvent) SetTimestamp() {
	now := time.Now().UnixMilli()
	h.Timestamp = &now
}

func (t *Theme) SetTimestamps() {
	now := time.Now().UnixMilli()
	t.CreatedAt = now
	t.UpdatedAt = now
}

func (t *Theme) UpdateTimestamp() {
	t.UpdatedAt = time.Now().UnixMilli()
}
