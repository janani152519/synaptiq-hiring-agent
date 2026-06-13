# Build the React Frontend
FROM node:22 AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Build the FastAPI Backend
FROM python:3.11

# Hugging Face Spaces MUST run as a non-root user (UID 1000)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /home/user/app

# Install python dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY --chown=user . .

# Copy built frontend static files into the backend static folder
RUN mkdir -p backend/static
COPY --chown=user --from=frontend-builder /build/backend/static ./backend/static

# Expose the port Hugging Face Spaces expects
EXPOSE 7860

# Run the FastAPI server on port 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
