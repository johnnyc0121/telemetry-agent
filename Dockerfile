FROM python:3.14.5-trixie

# Install updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends iputils-ping traceroute && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /app

# Copy the entire local directory into the container inside /app
COPY agent/ ./agent/

# Set up Python environment
COPY agent/requirements.txt .
RUN pip3 install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Execute the application
CMD ["python", "-m", "agent.main"]
