# Use the official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and application code to the container
COPY requirements.txt /app/
COPY . /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port (5000)
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
