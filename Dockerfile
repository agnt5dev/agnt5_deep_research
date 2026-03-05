# AGNT5 SDK Python Benchmark Blueprint
FROM debian:stable-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1001 agnt5 && \
    chown -R agnt5:agnt5 /app

# Copy application code
COPY --chown=agnt5:agnt5 app.py ./
COPY --chown=agnt5:agnt5 src ./src

# Set Python path to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Switch to non-root user
USER agnt5

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Expose port (will be set by deployment)
EXPOSE 8000

# Run the worker
CMD ["python", "app.py"]
