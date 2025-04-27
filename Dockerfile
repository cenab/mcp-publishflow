# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on (FastMCP default is 8000)
EXPOSE 8000

# Expose the port for Prometheus metrics (default is 9090)
EXPOSE 9090

# Run the application
# Use the main script as the entry point
CMD ["python", "mcp_publish_server.py"]