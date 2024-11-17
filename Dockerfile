FROM python:3.12

# Install Poetry and PostgreSQL client for pg_isready
RUN apt-get update && apt-get install -y postgresql-client && \
    curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to the PATH
ENV PATH="/root/.local/bin:$PATH"

# Set the working directory
WORKDIR /app

# Copy the project files and set permissions for entrypoint.sh in a single layer
COPY pyproject.toml poetry.lock /app/
COPY api /app/api
COPY manage.py /app/manage.py
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x entrypoint.sh  # 755 ensures read, write, and execute permissions for the owner, and read + execute for others

# Install dependencies using Poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

# Install watchdog to enable hot reloading
RUN poetry run pip install watchdog

# Set environment variables for Django
ENV PYTHONUNBUFFERED=1

# Use entrypoint.sh as the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
