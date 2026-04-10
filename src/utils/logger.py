import logging
import sys
import os

def get_logger(name: str) -> logging.Logger:
    """
    Returns a pre-configured logger for the ATS model.
    Logs INFO and above to stdout, and DEBUG and above to a file.
    """
    logger = logging.getLogger(name)
    
    # Avoid attaching duplicate handlers if already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Command line output handler
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.INFO)
    c_format = logging.Formatter('%(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)

    # File output handler
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    f_handler = logging.FileHandler(os.path.join(log_dir, 'ats_evaluator.log'))
    f_handler.setLevel(logging.DEBUG)
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(f_format)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger
