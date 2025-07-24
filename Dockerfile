# Use an official Python runtime as a parent image.
# Using a specific slim-buster version for smaller image size and reproducibility.
FROM python:3.9-slim-buster

# Set the working directory in the container.
WORKDIR /app

# Copy only the requirements file first to leverage Docker's layer caching.
# If requirements.txt doesn't change, this layer won't be rebuilt.
COPY requirements.txt .

# Install any needed packages specified in requirements.txt.
# --no-cache-dir: Prevents pip from caching downloaded packages, reducing image size.
# --upgrade pip: Ensures pip is up-to-date.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Explicitly copy your Streamlit application file.
COPY app.py .

# Explicitly copy your PDF file.
# Ensure 'PaymentAuthorizationRequestforReimbursement.pdf' is in the same directory as your Dockerfile.
COPY PaymentAuthorizationRequestforReimbursement.pdf .

# Expose the port that Streamlit will run on.
# Cloud Run expects applications to listen on port 8080 by default.
EXPOSE 8080

# Define the command to run your Streamlit application.
# ENTRYPOINT is used here to ensure the Streamlit command is always executed.
# --server.port=8080: Tells Streamlit to listen on port 8080.
# --server.address=0.0.0.0: Tells Streamlit to listen on all available network interfaces,
#                           crucial for Cloud Run to route traffic to your app.
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
