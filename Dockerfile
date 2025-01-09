FROM openjdk:17-slim

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Download Synthea
RUN wget https://github.com/synthetichealth/synthea/releases/download/v3.3.0/synthea-with-dependencies.jar && \
    chmod +x synthea-with-dependencies.jar

# Download SLF4J logger and API
RUN wget -O /app/slf4j-api.jar https://repo1.maven.org/maven2/org/slf4j/slf4j-api/1.7.36/slf4j-api-1.7.36.jar && \
    wget -O /app/slf4j-simple.jar https://repo1.maven.org/maven2/org/slf4j/slf4j-simple/1.7.36/slf4j-simple-1.7.36.jar

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ ./app/
COPY static/ ./static/

# Create output directory and ensure proper permissions
RUN mkdir -p /app/output && \
    chmod -R 777 /app/output && \
    chmod -R 777 /app

# Copy properties file
COPY app/synthea.properties ./app/synthea.properties

# Set environment variables
ENV PYTHONPATH=/app
ENV CLASSPATH=/app/synthea-with-dependencies.jar:/app/slf4j-api.jar:/app/slf4j-simple.jar
ENV JAVA_OPTS="-Dorg.slf4j.simpleLogger.defaultLogLevel=warn -Dorg.slf4j.simpleLogger.log.org.reflections=error"

# Expose port
EXPOSE 8000

# Run the application
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
