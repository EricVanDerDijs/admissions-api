# Use an official Python runtime as a parent image
FROM python:3.6

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Define environment variable
ENV REPLICAS_ADDRESSES '[ ["172.17.0.1", 3010], ["172.17.0.1", 3020], ["172.17.0.1", 3030] ]'
ENV REPLICAS_SECRET 4c87e4bff577ebcfdf3bfba539ce4d2fffe9461da75599db67f70885b981a00f
ENV SECRET XQ2xWkLgwTD4z9LL6WxV5erNUgshPXYv
ENV INIT_DB True

# Run app.py when the container launches
CMD ["python", "app.py"]
