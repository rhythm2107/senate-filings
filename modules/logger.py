import logging
import os

def setup_logger(name, log_filename="my_script.log"):
    # Always write logs to the 'debug' folder.
    debug_folder = f"debug/"
    if not os.path.exists(debug_folder):
        os.makedirs(debug_folder)

    # Build a filename with the account name as prefix.
    full_filename = f"{log_filename}"

    # Prepend the folder to the filename.
    log_filename = os.path.join(debug_folder, full_filename)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all log levels

    log_format = "%(asctime)s | %(levelname)-8s | %(message)s"
    
    console_formatter = logging.Formatter(log_format, "%H:%M:%S")
    file_formatter = logging.Formatter(log_format, "%Y-%m-%d %H:%M:%S")

    # # -- Filter to ONLY include INFO messages (used for console)
    # class OnlyInfoFilter(logging.Filter):
    #     def filter(self, record):
    #         return record.levelno == logging.INFO

    # -- Filter to EXCLUDE INFO messages (used for file)
    class ExcludeInfoFilter(logging.Filter):
        def filter(self, record):
            return record.levelno != logging.INFO

    # -----------------------
    # Console Handler
    # -----------------------
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.DEBUG)  # We'll handle all levels, then filter
    # console_handler.setFormatter(console_formatter)
    # console_handler.addFilter(OnlyInfoFilter())  # Only pass INFO to console

    # -----------------------
    # File Handler
    # -----------------------
    file_handler = logging.FileHandler(log_filename, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Capture everything
    file_handler.setFormatter(file_formatter)
    # Uncomment the next line if you want to exclude INFO from the file:
    # file_handler.addFilter(ExcludeInfoFilter())

    # -----------------------
    # Cleanup old handlers (if any), add new ones
    # -----------------------
    if logger.hasHandlers():
        logger.handlers.clear()

    # logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Prevent logs from propagating to the root logger
    logger.propagate = False

    return logger
