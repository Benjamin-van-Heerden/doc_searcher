import logging
import sys
from cfg import LOGFILE_PATH


def setup_stdout_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(process)d : %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def setup_file_logging(filename):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(process)d : %(message)s",
        filename=LOGFILE_PATH,
        filemode="a",
    )
