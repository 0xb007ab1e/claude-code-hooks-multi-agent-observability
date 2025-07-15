use axum_skeleton::create_app;
use std::env;
use std::net::SocketAddr;
use tokio;
use tracing_subscriber;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    if let Err(_) = dotenv::dotenv() {
        eprintln!("Failed to read .env file or .env not present");
    }

    // Build our application by composing routes
    let app = create_app();

    // Bind the app to a socket address
    let port = env::var("PORT").unwrap_or_else(|_| "8090".to_string());
    let addr = SocketAddr::from(([127, 0, 0, 1], port.parse().unwrap()));
    tracing::debug!("listening on {}", addr);

    // Run the server with the tokio listener
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
