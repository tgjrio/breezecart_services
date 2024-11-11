# Start with a lightweight Python base image
FROM python:3.11-slim

# Set environment variables to avoid interactive prompts and ensure non-root usage
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy only requirements first to leverage Docker caching
COPY breezecart/requirements.txt ./requirements.txt

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the remaining application code
COPY . .

# Set PYTHONPATH to the root of the project
ENV PYTHONPATH=/app

# Expose the port FastAPI will run on
EXPOSE 8000

# Accept SERVICE_NAME as an environment variable
ARG SERVICE_NAME
ENV SERVICE_NAME=${SERVICE_NAME}

# Run the FastAPI application using Uvicorn
CMD ["sh", "-c", "uvicorn ${SERVICE_NAME}.main:app --host 0.0.0.0 --port $PORT"]