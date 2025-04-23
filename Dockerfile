FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . .

RUN uv sync --locked

# Create a non-root user
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Create entrypoint script
RUN echo '#!/bin/bash\n\
echo "Initializing schema..."\n\
uv run dgraph/init_schema.py\n\
echo "Starting API server..."\n\
uv run uvicorn api.app:app --host $API_HOST --port $API_PORT\n' > /app/entrypoint.sh && \
chmod +x /app/entrypoint.sh

# Run the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]