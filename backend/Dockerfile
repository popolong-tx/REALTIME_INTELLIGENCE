FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# The build context is the repository root so one image contains the API and UI.
COPY backend/requirements-ui.txt /tmp/requirements-ui.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements-ui.txt

# Copy application code
COPY backend /app/backend
COPY frontend/public /app/frontend/public

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main_ui:app", "--host", "0.0.0.0", "--port", "8000"]
