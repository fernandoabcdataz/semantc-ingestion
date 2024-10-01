import logging
import structlog
import sys

def get_logger() -> structlog.BoundLogger:
    """
    Initializes and returns a structured logger.

    Returns:
        structlog.BoundLogger: The configured logger.
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )

    return structlog.get_logger()