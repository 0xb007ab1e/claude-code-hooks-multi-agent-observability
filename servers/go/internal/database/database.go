package database

import (
	"database/sql"
	"encoding/json"
	"fmt"

	_ "github.com/mattn/go-sqlite3"
	"github.com/sirupsen/logrus"

	"multi-agent-observability-server-go/pkg/models"
)

// Database represents the database connection and operations
type Database struct {
	db *sql.DB
}

// DatabaseInterface defines the database operations
type DatabaseInterface interface {
	InitDatabase() error
	Close() error
	InsertEvent(event *models.HookEvent) (*models.HookEvent, error)
	GetRecentEvents(limit, offset int) ([]*models.HookEvent, error)
	GetFilterOptions() (*models.FilterOptions, error)
	GetEventCount() (int64, error)
	CreateTheme(theme *models.Theme) (*models.ApiResponse, error)
	GetThemeByID(themeID string) (*models.ApiResponse, error)
	SearchThemes(query *models.ThemeSearchQuery) (*models.ApiResponse, error)
}

// NewDatabase creates a new database instance
func NewDatabase(dbPath string) (*Database, error) {
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	database := &Database{db: db}
	
	if err := database.InitDatabase(); err != nil {
		return nil, fmt.Errorf("failed to initialize database: %w", err)
	}

	return database, nil
}

// InitDatabase initializes the database with required tables
func (d *Database) InitDatabase() error {
	// Create events table
	eventsTable := `
		CREATE TABLE IF NOT EXISTS events (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			source_app TEXT NOT NULL,
			session_id TEXT NOT NULL,
			hook_event_type TEXT NOT NULL,
			payload TEXT NOT NULL,
			chat TEXT,
			summary TEXT,
			timestamp INTEGER NOT NULL
		)
	`

	// Create themes table
	themesTable := `
		CREATE TABLE IF NOT EXISTS themes (
			id TEXT PRIMARY KEY,
			name TEXT NOT NULL,
			displayName TEXT NOT NULL,
			description TEXT,
			colors TEXT NOT NULL,
			isPublic BOOLEAN NOT NULL,
			authorId TEXT,
			authorName TEXT,
			createdAt INTEGER NOT NULL,
			updatedAt INTEGER NOT NULL,
			tags TEXT NOT NULL,
			downloadCount INTEGER DEFAULT 0,
			rating REAL,
			ratingCount INTEGER DEFAULT 0
		)
	`

	// Create indexes
	indexes := []string{
		"CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)",
		"CREATE INDEX IF NOT EXISTS idx_events_source_app ON events(source_app)",
		"CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id)",
		"CREATE INDEX IF NOT EXISTS idx_events_hook_event_type ON events(hook_event_type)",
		"CREATE INDEX IF NOT EXISTS idx_themes_name ON themes(name)",
		"CREATE INDEX IF NOT EXISTS idx_themes_author ON themes(authorId)",
		"CREATE INDEX IF NOT EXISTS idx_themes_public ON themes(isPublic)",
	}

	// Execute table creation
	if _, err := d.db.Exec(eventsTable); err != nil {
		return fmt.Errorf("failed to create events table: %w", err)
	}

	if _, err := d.db.Exec(themesTable); err != nil {
		return fmt.Errorf("failed to create themes table: %w", err)
	}

	// Execute index creation
	for _, index := range indexes {
		if _, err := d.db.Exec(index); err != nil {
			return fmt.Errorf("failed to create index: %w", err)
		}
	}

	logrus.Info("✅ Database initialized successfully")
	return nil
}

// Close closes the database connection
func (d *Database) Close() error {
	return d.db.Close()
}

// InsertEvent inserts a new event into the database
func (d *Database) InsertEvent(event *models.HookEvent) (*models.HookEvent, error) {
	if event.Timestamp == nil {
		event.SetTimestamp()
	}

	payloadJSON, err := event.PayloadJSON()
	if err != nil {
		return nil, fmt.Errorf("failed to marshal payload: %w", err)
	}

	var chatJSON []byte
	if event.Chat != nil {
		chatJSON, err = event.ChatJSON()
		if err != nil {
			return nil, fmt.Errorf("failed to marshal chat: %w", err)
		}
	}

	query := `
		INSERT INTO events (source_app, session_id, hook_event_type, payload, chat, summary, timestamp)
		VALUES (?, ?, ?, ?, ?, ?, ?)
	`

	result, err := d.db.Exec(query, event.SourceApp, event.SessionID, event.HookEventType, 
		string(payloadJSON), string(chatJSON), event.Summary, *event.Timestamp)
	if err != nil {
		return nil, fmt.Errorf("failed to insert event: %w", err)
	}

	id, err := result.LastInsertId()
	if err != nil {
		return nil, fmt.Errorf("failed to get last insert id: %w", err)
	}

	event.ID = &id
	return event, nil
}

// GetRecentEvents retrieves recent events from the database
func (d *Database) GetRecentEvents(limit, offset int) ([]*models.HookEvent, error) {
	query := `
		SELECT id, source_app, session_id, hook_event_type, payload, chat, summary, timestamp
		FROM events
		ORDER BY timestamp DESC
		LIMIT ? OFFSET ?
	`

	rows, err := d.db.Query(query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to query events: %w", err)
	}
	defer rows.Close()

	var events []*models.HookEvent
	for rows.Next() {
		event := &models.HookEvent{}
		var payloadJSON, chatJSON sql.NullString

		err := rows.Scan(&event.ID, &event.SourceApp, &event.SessionID, &event.HookEventType,
			&payloadJSON, &chatJSON, &event.Summary, &event.Timestamp)
		if err != nil {
			return nil, fmt.Errorf("failed to scan event: %w", err)
		}

		// Parse JSON fields
		if payloadJSON.Valid {
			if err := json.Unmarshal([]byte(payloadJSON.String), &event.Payload); err != nil {
				return nil, fmt.Errorf("failed to unmarshal payload: %w", err)
			}
		}

		if chatJSON.Valid {
			if err := json.Unmarshal([]byte(chatJSON.String), &event.Chat); err != nil {
				return nil, fmt.Errorf("failed to unmarshal chat: %w", err)
			}
		}

		events = append(events, event)
	}

	return events, nil
}

// GetFilterOptions retrieves available filter options
func (d *Database) GetFilterOptions() (*models.FilterOptions, error) {
	// Get unique source apps
	sourceApps, err := d.getUniqueValues("SELECT DISTINCT source_app FROM events ORDER BY source_app")
	if err != nil {
		return nil, fmt.Errorf("failed to get source apps: %w", err)
	}

	// Get unique session IDs
	sessionIDs, err := d.getUniqueValues("SELECT DISTINCT session_id FROM events ORDER BY session_id")
	if err != nil {
		return nil, fmt.Errorf("failed to get session IDs: %w", err)
	}

	// Get unique hook event types
	hookEventTypes, err := d.getUniqueValues("SELECT DISTINCT hook_event_type FROM events ORDER BY hook_event_type")
	if err != nil {
		return nil, fmt.Errorf("failed to get hook event types: %w", err)
	}

	return &models.FilterOptions{
		SourceApps:     sourceApps,
		SessionIDs:     sessionIDs,
		HookEventTypes: hookEventTypes,
	}, nil
}

// getUniqueValues is a helper function to get unique values from a query
func (d *Database) getUniqueValues(query string) ([]string, error) {
	rows, err := d.db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var values []string
	for rows.Next() {
		var value string
		if err := rows.Scan(&value); err != nil {
			return nil, err
		}
		values = append(values, value)
	}

	return values, nil
}

// GetEventCount retrieves the total count of events
func (d *Database) GetEventCount() (int64, error) {
	var count int64
	err := d.db.QueryRow("SELECT COUNT(*) FROM events").Scan(&count)
	if err != nil {
		return 0, fmt.Errorf("failed to get event count: %w", err)
	}
	return count, nil
}

// CreateTheme creates a new theme in the database
func (d *Database) CreateTheme(theme *models.Theme) (*models.ApiResponse, error) {
	// Check if theme already exists
	var exists bool
	err := d.db.QueryRow("SELECT EXISTS(SELECT 1 FROM themes WHERE id = ?)", theme.ID).Scan(&exists)
	if err != nil {
		errorMsg := fmt.Sprintf("Database error: %v", err)
		return &models.ApiResponse{
			Success: false,
			Error:   &errorMsg,
		}, nil
	}

	if exists {
		errorMsg := fmt.Sprintf("Theme with ID %s already exists", theme.ID)
		return &models.ApiResponse{
			Success: false,
			Error:   &errorMsg,
		}, nil
	}

	// Set timestamps if not set
	if theme.CreatedAt == 0 || theme.UpdatedAt == 0 {
		theme.SetTimestamps()
	}

	colorsJSON, err := theme.ColorsJSON()
	if err != nil {
		errorMsg := fmt.Sprintf("Failed to marshal colors: %v", err)
		return &models.ApiResponse{
			Success: false,
			Error:   &errorMsg,
		}, nil
	}

	tagsJSON, err := theme.TagsJSON()
	if err != nil {
		errorMsg := fmt.Sprintf("Failed to marshal tags: %v", err)
		return &models.ApiResponse{
			Success: false,
			Error:   &errorMsg,
		}, nil
	}

	query := `
		INSERT INTO themes (id, name, displayName, description, colors, isPublic, 
		                   authorId, authorName, createdAt, updatedAt, tags, 
		                   downloadCount, rating, ratingCount)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	`

	_, err = d.db.Exec(query, theme.ID, theme.Name, theme.DisplayName, theme.Description,
		string(colorsJSON), theme.IsPublic, theme.AuthorID, theme.AuthorName,
		theme.CreatedAt, theme.UpdatedAt, string(tagsJSON),
		theme.DownloadCount, theme.Rating, theme.RatingCount)
	if err != nil {
		errorMsg := fmt.Sprintf("Failed to insert theme: %v", err)
		return &models.ApiResponse{
			Success: false,
			Error:   &errorMsg,
		}, nil
	}

	successMsg := "Theme created successfully"
	return &models.ApiResponse{
		Success: true,
		Data:    theme,
		Message: &successMsg,
	}, nil
}

// GetThemeByID retrieves a theme by its ID
func (d *Database) GetThemeByID(themeID string) (*models.ApiResponse, error) {
	query := `
		SELECT id, name, displayName, description, colors, isPublic, authorId, authorName,
		       createdAt, updatedAt, tags, downloadCount, rating, ratingCount
		FROM themes WHERE id = ?
	`

	theme := &models.Theme{}
	var colorsJSON, tagsJSON string

	err := d.db.QueryRow(query, themeID).Scan(
		&theme.ID, &theme.Name, &theme.DisplayName, &theme.Description,
		&colorsJSON, &theme.IsPublic, &theme.AuthorID, &theme.AuthorName,
		&theme.CreatedAt, &theme.UpdatedAt, &tagsJSON,
		&theme.DownloadCount, &theme.Rating, &theme.RatingCount)
	if err != nil {
		if err == sql.ErrNoRows {
			errorMsg := "Theme not found"
			return &models.ApiResponse{
				Success: false,
				Error:   &errorMsg,
			}, nil
		}
		errorMsg := fmt.Sprintf("Database error: %v", err)
		return &models.ApiResponse{
			Success: false,
			Error:   &errorMsg,
		}, nil
	}

	// Parse JSON fields
	if err := json.Unmarshal([]byte(colorsJSON), &theme.Colors); err != nil {
		errorMsg := fmt.Sprintf("Failed to unmarshal colors: %v", err)
		return &models.ApiResponse{
			Success: false,
			Error:   &errorMsg,
		}, nil
	}

	if err := json.Unmarshal([]byte(tagsJSON), &theme.Tags); err != nil {
		errorMsg := fmt.Sprintf("Failed to unmarshal tags: %v", err)
		return &models.ApiResponse{
			Success: false,
			Error:   &errorMsg,
		}, nil
	}

	return &models.ApiResponse{
		Success: true,
		Data:    theme,
	}, nil
}

// SearchThemes searches for themes based on query parameters
func (d *Database) SearchThemes(query *models.ThemeSearchQuery) (*models.ApiResponse, error) {
	// Build WHERE clause
	var whereConditions []string
	var args []interface{}

	if query.Query != nil && *query.Query != "" {
		whereConditions = append(whereConditions, "(name LIKE ? OR displayName LIKE ? OR description LIKE ?)")
		searchTerm := fmt.Sprintf("%%%s%%", *query.Query)
		args = append(args, searchTerm, searchTerm, searchTerm)
	}

	if query.AuthorID != nil {
		whereConditions = append(whereConditions, "authorId = ?")
		args = append(args, *query.AuthorID)
	}

	if query.IsPublic != nil {
		whereConditions = append(whereConditions, "isPublic = ?")
		args = append(args, *query.IsPublic)
	}

	whereClause := ""
	if len(whereConditions) > 0 {
		whereClause = "WHERE " + fmt.Sprintf("%s", whereConditions[0])
		for i := 1; i < len(whereConditions); i++ {
			whereClause += " AND " + whereConditions[i]
		}
	}

	// Build ORDER BY clause
	orderBy := "ORDER BY name ASC"
	if query.SortBy != nil {
		direction := "ASC"
		if query.SortOrder != nil && *query.SortOrder == "desc" {
			direction = "DESC"
		}

		switch *query.SortBy {
		case "created":
			orderBy = fmt.Sprintf("ORDER BY createdAt %s", direction)
		case "updated":
			orderBy = fmt.Sprintf("ORDER BY updatedAt %s", direction)
		case "downloads":
			orderBy = fmt.Sprintf("ORDER BY downloadCount %s", direction)
		case "rating":
			orderBy = fmt.Sprintf("ORDER BY rating %s", direction)
		default:
			orderBy = fmt.Sprintf("ORDER BY name %s", direction)
		}
	}

	// Build LIMIT and OFFSET
	limit := 10
	offset := 0
	if query.Limit != nil {
		limit = *query.Limit
	}
	if query.Offset != nil {
		offset = *query.Offset
	}

	sqlQuery := fmt.Sprintf(`
		SELECT id, name, displayName, description, colors, isPublic, authorId, authorName,
		       createdAt, updatedAt, tags, downloadCount, rating, ratingCount
		FROM themes
		%s
		%s
		LIMIT ? OFFSET ?
	`, whereClause, orderBy)

	args = append(args, limit, offset)

	rows, err := d.db.Query(sqlQuery, args...)
	if err != nil {
		errorMsg := fmt.Sprintf("Database error: %v", err)
		return &models.ApiResponse{
			Success: false,
			Error:   &errorMsg,
		}, nil
	}
	defer rows.Close()

	var themes []*models.Theme
	for rows.Next() {
		theme := &models.Theme{}
		var colorsJSON, tagsJSON string

		err := rows.Scan(&theme.ID, &theme.Name, &theme.DisplayName, &theme.Description,
			&colorsJSON, &theme.IsPublic, &theme.AuthorID, &theme.AuthorName,
			&theme.CreatedAt, &theme.UpdatedAt, &tagsJSON,
			&theme.DownloadCount, &theme.Rating, &theme.RatingCount)
		if err != nil {
			errorMsg := fmt.Sprintf("Failed to scan theme: %v", err)
			return &models.ApiResponse{
				Success: false,
				Error:   &errorMsg,
			}, nil
		}

		// Parse JSON fields
		if err := json.Unmarshal([]byte(colorsJSON), &theme.Colors); err != nil {
			errorMsg := fmt.Sprintf("Failed to unmarshal colors: %v", err)
			return &models.ApiResponse{
				Success: false,
				Error:   &errorMsg,
			}, nil
		}

		if err := json.Unmarshal([]byte(tagsJSON), &theme.Tags); err != nil {
			errorMsg := fmt.Sprintf("Failed to unmarshal tags: %v", err)
			return &models.ApiResponse{
				Success: false,
				Error:   &errorMsg,
			}, nil
		}

		themes = append(themes, theme)
	}

	return &models.ApiResponse{
		Success: true,
		Data:    themes,
	}, nil
}
