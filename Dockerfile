# Build the React Frontend
FROM node:18 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Build the FastAPI Backend
FROM python:3.11-slim
WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Copy built frontend static files into the backend static folder
RUN mkdir -p backend/static
COPY --from=frontend-builder /app/frontend/dist ./backend/static

# Expose the port Hugging Face Spaces expects
EXPOSE 7860

# Run the FastAPI server on port 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
