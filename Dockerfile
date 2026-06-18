# syntax=docker/dockerfile:1

# Latest stable Python on a small Debian base.
FROM python:3.13-slim

# Keep Python output unbuffered and skip writing .pyc files in the container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements change.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project source.
COPY . .

# Default to running the test suite; override the command to run the CLI.
CMD ["pytest"]
