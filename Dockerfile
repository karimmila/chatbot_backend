# Use official Python image as a base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run the LangServe API
CMD ["python", "app.py"]