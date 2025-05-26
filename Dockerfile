FROM python:3.13d-slim

# Create app directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 5000

# Run your app
CMD ["python", "app.py"]
