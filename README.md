# MCP Publish Flow

This project implements a Model Context Protocol (MCP) server that enables automated publishing of content to Substack and Medium platforms with advanced features for content management, security, and monitoring.

## Features

- **Content Management**
  - Markdown file processing with frontmatter support
  - Image handling and upload
  - Content validation and sanitization
  - Support for drafts and revisions

- **Security**
  - JWT-based authentication
  - Rate limiting
  - Request validation
  - Secure environment variable handling

- **Monitoring**
  - Prometheus metrics integration
  - Health checks
  - System metrics collection
  - Error tracking and logging

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Copy the `.env.example` file to `.env` and update the values with your configuration:
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file:
   ```
   # API Keys
   SUBSTACK_API_KEY=your-substack-api-key
   MEDIUM_API_KEY=your-medium-api-key

   # Security
   SECRET_KEY=your-secret-key
   REDIS_URL=redis://localhost:6379

   # Monitoring
   METRICS_PORT=9090

   # Image Upload
   IMAGE_UPLOAD_URL=https://your-image-service.com/upload
   ```

3. **Run the MCP Server Locally**:
   ```bash
   python mcp_publish_server.py
   ```
   The server will run locally on port 8000.

4. **Run with Docker**:
   If you have Docker and Docker Compose installed, you can build and run the application using the provided `Dockerfile` and `docker-compose.yml`.

   a. **Build the Docker image**:
      ```bash
      docker-compose build
      ```

   b. **Run the container**:
      ```bash
      docker-compose up
      ```
      This will start the MCP server and any other services defined in `docker-compose.yml` (e.g., Redis). The server will be accessible at `http://localhost:8000` and metrics at `http://localhost:9090`.

   c. **Run in detached mode**:
      To run the containers in the background:
      ```bash
      docker-compose up -d
      ```

   d. **Stop the containers**:
      ```bash
      docker-compose down
      ```

## Configuration

### For Claude Desktop
Update `~/Library/ApplicationSupport/Claude/claude_desktop_config.json` (on macOS) to include:
```json
{
  "mcp_servers": [
    {
      "url": "http://localhost:8000",
      "name": "publish_server"
    }
  ]
}
```

### For Cursor
1. Go to Settings > Cursor Settings > MCP
2. Add new global MCP server
3. Enter `http://localhost:8000`

## Usage

The server provides several tools:

1. **publish_to_substack**: Publish content to Substack
   - Parameters:
     - `file_path`: Path to the markdown file
     - `title`: Post title
     - `subtitle`: Optional subtitle
     - `is_paid`: Whether the post is for paid subscribers

2. **publish_to_medium**: Publish content to Medium
   - Parameters:
     - `file_path`: Path to the markdown file
     - `title`: Post title
     - `tags`: List of tags for the post
     - `public`: Whether the post is public or draft

3. **read_codebase_file**: Read a markdown file from the codebase
   - Parameters:
     - `file_path`: Path to the markdown file

4. **health_check**: Check service health status
   - Returns system metrics and health information

## Markdown Format

The server supports markdown files with YAML frontmatter for metadata:

```markdown
---
title: My Post Title
subtitle: A great subtitle
tags: [tech, coding]
date: 2024-01-01
draft: false
---

# Main Content

Your markdown content here...
```

## Monitoring

The server exposes Prometheus metrics on port 9090 (configurable). Available metrics:

- `mcp_publish_requests_total`: Total number of requests
- `mcp_publish_errors_total`: Total number of errors
- `mcp_publish_latency_seconds`: Publishing latency
- `mcp_publish_memory_bytes`: Memory usage
- `mcp_publish_cpu_percent`: CPU usage

## Security

- All endpoints require authentication via JWT tokens
- Rate limiting is enforced per endpoint
- Content is validated and sanitized before publishing
- Sensitive data is properly handled and logged

## Example Commands

- "Publish article.md to Substack with title 'My New Post' and subtitle 'A great read' for paid subscribers"
- "Publish article.md to Medium with title 'My Tech Post' and tags ['tech', 'coding'] as public"
- "Check service health status"

## Notes

- The server uses placeholder API endpoints that need to be updated based on the actual Substack and Medium API documentation
- Ensure your API keys are valid and have the necessary permissions
- The server runs locally; for production use, consider adding authentication and running over HTTPS
- Image upload requires a compatible image service
- Redis is required for rate limiting