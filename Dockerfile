# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy everything from here to container
COPY . .

# Install git -commented for testing
# RUN apt update && apt install -y git

# Clone your repository -commented for testing
# RUN git clone https://github.com/nataliarogoza/devops-mini-project.git .

# Install dependencies
RUN pip install -r requirements.txt

# Expose Flask port
EXPOSE 5000

# Run the app
CMD ["python", "main.py"]
