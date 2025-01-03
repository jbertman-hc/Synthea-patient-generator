FROM openjdk:17-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create output directory and set permissions
RUN mkdir -p /app/output && \
    chmod 777 /app/output && \
    chown -R nobody:nogroup /app/output

# Download and setup Synthea
RUN wget https://github.com/synthetichealth/synthea/releases/download/v3.3.0/synthea-with-dependencies.jar \
    && chmod +x synthea-with-dependencies.jar

# Copy the Python application
COPY requirements.txt .
COPY app/ ./app/
COPY static/ ./static/

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Change ownership of the application files
RUN chown -R nobody:nogroup /app

# Switch to non-root user
USER nobody

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
