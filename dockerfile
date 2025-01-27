# Use the official Python image as the base image
FROM python:3.12-slim

# # Set environment variables
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /home/app

# Copy the requirements file to the working directory
COPY requirements.txt /home/app/

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the project files to the container
COPY . /home/app/

# Expose the port Django runs on
EXPOSE 8000

# Run the Django development server (customize if needed for production)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
