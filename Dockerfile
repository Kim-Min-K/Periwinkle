FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app/periwinkleposts 
# needed for guincorn^

# Set work directory
WORKDIR /app
#WORKDIR /app/periwinkleposts

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package.json and install Node.js dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy the rest of the application
COPY . .

# tailwind stuff
RUN npm install -D tailwindcss
RUN npx tailwindcss -i periwinkleposts/static/main.css -o periwinkleposts/static/output.css

# static stuff
RUN python periwinkleposts/manage.py collectstatic --noinput

#create directory for SQLite database
RUN mkdir -p /app/db

#expose port for the application
EXPOSE 8000

# run with gunicorn
CMD ["gunicorn", "--workers=1", "--bind", "0.0.0.0:8000", "periwinkleposts.wsgi:application"]