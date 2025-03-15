from dataclasses import dataclass
from pydantic import BaseModel, Field
import os


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT_DIR, "logs")
LOGFILE_PATH = os.path.join(LOG_DIR, "log.log")
os.makedirs(LOG_DIR, exist_ok=True)
if not os.path.exists(LOGFILE_PATH):
    with open(LOGFILE_PATH, "w") as f:
        f.write("")

STORAGE_DIR = os.path.join(ROOT_DIR, "db")
os.makedirs(STORAGE_DIR, exist_ok=True)
DOCS_DIR = os.path.join(STORAGE_DIR, "docs")
os.makedirs(DOCS_DIR, exist_ok=True)
SUMMARIES_DIR = os.path.join(STORAGE_DIR, "summaries")
os.makedirs(SUMMARIES_DIR, exist_ok=True)

DB_PATH = os.path.join(STORAGE_DIR, "db.sqlite")
USELESS_DIR = os.path.join(STORAGE_DIR, "useless")
os.makedirs(USELESS_DIR, exist_ok=True)


@dataclass
class IOConfig:
    root_dir: str = ROOT_DIR
    storage_dir: str = STORAGE_DIR
    docs_dir: str = DOCS_DIR
    summaries_dir: str = SUMMARIES_DIR
    db_path: str = DB_PATH
    useless_dir: str = USELESS_DIR


IO_CONFIG = IOConfig()
