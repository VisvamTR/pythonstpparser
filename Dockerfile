# Step 1: Use Anaconda as the base image
FROM continuumio/anaconda3

# Step 2: Set the working directory
WORKDIR /app

# Step 3: Copy the environment.yml file
COPY environment.yml .

# Step 4: Install the Conda environment
RUN conda env create -f environment.yml

# Step 5: Set the environment to be used by default
ENV PATH /opt/conda/envs/pythonstepparser/bin:$PATH

# Step 6: Copy the application code
COPY . .

# Step 7: Define the entry point for the application
CMD ["python", "app.py"]
