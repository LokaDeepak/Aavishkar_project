# Use official slim Python image
FROM python:3.10-slim

# Install system dependencies needed for pdf2image and pytesseract
RUN apt-get update && apt-get install -y poppler-utils tesseract-ocr && rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Copy Python dependencies file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port Streamlit listens on
EXPOSE 8501

# Command to run your Streamlit app
CMD ["streamlit", "run", "resume_new.py", "--server.port=8501", "--server.enableCORS=false"]
