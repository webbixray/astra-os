#!/usr/bin/env python3
"""Entrypoint script for Astra API container.
Handles database migrations, health checks, and graceful startup.
"""
import logging
import os
import subprocess
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("entrypoint")


def run_command(cmd: list, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env or os.environ, capture_output=True, text=True)
    if result.stdout:
        logger.info(result.stdout.strip())
    if result.stderr:
        logger.warning(result.stderr.strip())
    if check and result.returncode != 0:
        logger.error(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def wait_for_database(max_retries: int = 30, delay: float = 2.0) -> bool:
    """Wait for database to be ready."""
    from sqlalchemy import create_engine, text

    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/astra")
    logger.info(f"Waiting for database at {database_url}")

    for attempt in range(max_retries):
        try:
            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database is ready!")
            return True
        except Exception as e:
            logger.warning(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                logger.error("Max retries reached. Database unavailable.")
                return False
    return False


def wait_for_redis(max_retries: int = 30, delay: float = 2.0) -> bool:
    """Wait for Redis to be ready."""
    import redis

    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    logger.info(f"Waiting for Redis at {redis_url}")

    for attempt in range(max_retries):
        try:
            client = redis.from_url(redis_url)
            client.ping()
            logger.info("Redis is ready!")
            return True
        except Exception as e:
            logger.warning(f"Redis not ready (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                logger.error("Max retries reached. Redis unavailable.")
                return False
    return False


def run_migrations() -> bool:
    """Run database migrations."""
    logger.info("Running database migrations...")
    try:
        run_command(["alembic", "upgrade", "head"])
        logger.info("Migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def create_initial_data() -> bool:
    """Create initial data if needed (admin user, default org, etc.)."""
    logger.info("Checking for initial data setup...")
    # This could run a seed script or create default resources
    return True


def main():
    """Main entrypoint logic."""
    logger.info("=" * 60)
    logger.info("Astra API - Container Starting")
    logger.info("=" * 60)

    # Print environment info (sanitized)
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Python version: {sys.version}")

    # Wait for dependencies
    if not wait_for_database():
        sys.exit(1)

    if not wait_for_redis():
        sys.exit(1)

    # Run migrations
    if not run_migrations():
        sys.exit(1)

    # Create initial data
    if not create_initial_data():
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("Starting Astra API Server")
    logger.info("=" * 60)

    # Execute the main command (passed as arguments)
    if len(sys.argv) > 1:
        cmd = sys.argv[1:]
        logger.info(f"Executing command: {' '.join(cmd)}")
        os.execvp(cmd[0], cmd)
    else:
        # Default: start the server
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production":
            logger.info("Starting gunicorn server (production)...")
            os.execvpe(
                "gunicorn",
                [
                    "gunicorn",
                    "app.main:app",
                    "--worker-class", "uvicorn.workers.UvicornWorker",
                    "--bind", "0.0.0.0:8000",
                    "--workers", "4",
                    "--max-requests", "10000",
                    "--max-requests-jitter", "1000",
                    "--timeout", "60",
                    "--keep-alive", "5",
                    "--log-level", "info",
                    "--access-logfile", "-",
                    "--error-logfile", "-"
                ],
                os.environ
            )
        else:
            logger.info("Starting uvicorn server (development)...")
            os.execvpe(
                "python",
                ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                os.environ
            )


if __name__ == "__main__":
    main()
