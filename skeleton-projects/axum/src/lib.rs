use axum::{routing::get, Json, Router};
use chrono::Utc;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use tower_http::cors::CorsLayer;

#[derive(Serialize)]
pub struct Health {
    pub status: String,
    pub timestamp: String,
}

#[derive(Serialize)]
pub struct Message {
    pub message: String,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct User {
    pub id: usize,
    pub name: String,
    pub email: String,
}

#[derive(Serialize)]
pub struct UsersResponse {
    pub users: Vec<User>,
}

pub type UserStore = Arc<Mutex<HashMap<usize, User>>>;

pub async fn root() -> Json<Message> {
    Json(Message {
        message: "Axum skeleton API is running!".to_string(),
    })
}

pub async fn health() -> Json<Health> {
    Json(Health {
        status: "healthy".to_string(),
        timestamp: Utc::now().to_rfc3339(),
    })
}

pub async fn get_users() -> Json<UsersResponse> {
    Json(UsersResponse {
        users: vec![],
    })
}

pub fn create_app() -> Router {
    Router::new()
        .route("/", get(root))
        .route("/health", get(health))
        .route("/api/users", get(get_users))
        .layer(CorsLayer::permissive())
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum_test::TestServer;

    #[tokio::test]
    async fn test_root() {
        let app = create_app();
        let server = TestServer::new(app).unwrap();
        
        let response = server.get("/").await;
        response.assert_status_ok();
        
        let body: Message = response.json();
        assert_eq!(body.message, "Axum skeleton API is running!");
    }

    #[tokio::test]
    async fn test_health() {
        let app = create_app();
        let server = TestServer::new(app).unwrap();
        
        let response = server.get("/health").await;
        response.assert_status_ok();
        
        let body: Health = response.json();
        assert_eq!(body.status, "healthy");
        assert!(!body.timestamp.is_empty());
    }

    #[tokio::test]
    async fn test_get_users() {
        let app = create_app();
        let server = TestServer::new(app).unwrap();
        
        let response = server.get("/api/users").await;
        response.assert_status_ok();
        
        let body: UsersResponse = response.json();
        assert_eq!(body.users.len(), 0);
    }
}
