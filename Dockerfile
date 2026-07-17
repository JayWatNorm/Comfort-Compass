FROM python:3.12-slim

WORKDIR /app

# Copy requirements first so this layer only gets rebuilt when dependencies
# actually change, not on every code edit (Docker layer caching).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual project code.
COPY ingestion/ ingestion/
COPY dbt_project/ dbt_project/
COPY flask_app/ flask_app/
COPY docker/ docker/

# Points dbt at the env_var()-driven profiles.yml rather than ~/.dbt/,
# which won't exist inside the container.
ENV DBT_PROFILES_DIR=/app/docker

EXPOSE 5000

# Default command runs the Flask app; docker-compose overrides this
# per-service (e.g. the dbt service runs "dbt run" instead) since this
# same image is shared across services.
CMD ["python", "flask_app/app.py"]
