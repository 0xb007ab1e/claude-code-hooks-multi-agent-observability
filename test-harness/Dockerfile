FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    postgresql-client \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm for newman
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Install newman for Postman collection testing
RUN npm install -g newman

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test files
COPY . .

# Create reports directory
RUN mkdir -p reports

# Default command
CMD ["pytest", "-v"]
