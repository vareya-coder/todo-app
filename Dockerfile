# Use an official Python runtime as a parent image
FROM python:3.9.18-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV DATABASE_URL postgresql://vareya-coder:ozXZYqhHb0t3@ep-rapid-surf-a5dgaang-pooler.us-east-2.aws.neon.tech/maindb?sslmode=require

# Run app.py when the container launches
CMD ["uvicorn", "todo:app", "--host", "0.0.0.0", "--port", "8080"]
