# Dockerfile
FROM python:3.12

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to the PATH
ENV PATH="/root/.local/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy the project files
COPY pyproject.toml poetry.lock /app/
COPY api /app/api
COPY manage.py /app/manage.py

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

# Install watchdog to enable hot reloading
RUN poetry run pip install watchdog

# Set environment variables for Django
ENV PYTHONUNBUFFERED=1

# Run the Django development server with hot reloading
CMD ["poetry", "run", "watchmedo", "auto-restart", "--directory=.", "--pattern=*.py", "--recursive", "--", "python", "manage.py", "runserver", "0.0.0.0:8000"]
