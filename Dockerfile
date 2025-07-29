# Use a Conda-enabled base image.
# mambaforge is recommended for faster builds compared to miniconda/anaconda.
# We'll let environment.yml dictate the Python version.
FROM condaforge/mambaforge:latest

# Set the working directory in the container.
WORKDIR /app

# Copy the environment.yml file into the container.
# This allows Docker to cache this layer.
COPY environment.yml .

# Create the Conda environment from environment.yml.
# -n base: Install into the base environment (simpler for single-app containers).
# --file: Specify the environment file.
# --yes: Auto-accept prompts.
# This step will install Python 3.12 and pip (and any other conda-specified packages).
RUN mamba env update --name base --file environment.yml && \
    mamba clean --all --yes # Clean up unnecessary files to reduce image size

# Activate the base environment for subsequent commands.
# This ensures that the Python and packages from your Conda env are used.
SHELL ["conda", "run", "-n", "base", "/bin/bash", "-c"]

# Copy requirements.txt AFTER the conda environment is set up.
# This allows pip to install into the correct environment.
COPY requirements.txt .

# Install any pip-specific packages.
# --no-cache-dir: Prevents pip from caching downloaded packages, reducing image size.
RUN pip install --no-cache-dir -r requirements.txt

# Explicitly copy your Streamlit application file.
COPY app.py .

# Explicitly copy your PDF file.
# Ensure 'PaymentAuthorizationRequestforReimbursement.pdf' is in the same directory as your Dockerfile.
COPY PaymentAuthorizationRequestforReimbursement.pdf .

# Expose the port that Streamlit will run on.
# Cloud Run expects applications to listen on port 8080 by default.
EXPOSE 8080

# Define the command to run your Streamlit application.
# Use 'conda run -n base' to execute Streamlit within the Conda environment.
ENTRYPOINT ["conda", "run", "-n", "base", "streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
