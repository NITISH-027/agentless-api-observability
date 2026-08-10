import logging
import sys

def setup_logging() -> None:
    """
    Configures application-wide logging formats and outputs.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Silence third-party logger noise if necessary
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
