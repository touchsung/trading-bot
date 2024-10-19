# Use a minimal base image for Python
FROM --platform=linux/amd64 python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

RUN pip install --upgrade pip

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Command to run the application with uvicorn
CMD ["python", "main.py"]