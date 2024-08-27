# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 7860 available to the world outside this container
EXPOSE 7860

# Define environment variables if needed
# Example: ENV GOOGLE_API_KEY="your-api-key-here"

# Run app.py when the container launches using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]
