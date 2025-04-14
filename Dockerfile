# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Install Node.js and npx
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Set working directory
WORKDIR /app

# Copy only necessary files for dependency installation first to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Cấu hình Poetry không tạo virtualenv
RUN poetry config virtualenvs.create false

# Update the lock file if pyproject.toml changed
RUN poetry lock

# Install Python dependencies with Poetry
RUN poetry install --no-root

# Copy the rest of the project files
COPY ./ ./

# Expose the Streamlit default port
EXPOSE 8501

# Run the Streamlit app
ENTRYPOINT ["streamlit", "run", "llama_mcp_streamlit/main.py", "--server.port=8501", "--server.address=0.0.0.0"]