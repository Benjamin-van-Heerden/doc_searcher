import os
from agents import summarizer
from agents.summarizer import get_summarizer_response
from cfg import IO_CONFIG
from scripts.db_init import db_init
from utils.loggers import setup_stdout_logging
from env import GEMINI_API_KEY
from typing import Tuple, List
from src.models.knowledge import KnowledgeBase, LLMResource, Resource
import asyncio
import math

import logging

logger = logging.getLogger(__name__)


def get_all_files_for_processing(knowledge_base):
    logger.info(f"Getting all files for processing from {knowledge_base}")
    names_files = []
    source_documents_dir = os.path.join(IO_CONFIG.docs_dir, knowledge_base)
    for root, dirs, filenames in os.walk(source_documents_dir):
        for filename in filenames:
            if filename.endswith(".md"):
                page_file = os.path.join(root, filename)
                names_files.append(
                    (
                        page_file.replace(source_documents_dir, "")
                        .replace("/page.md", "")
                        .replace(".html", "")
                        .lstrip("/")
                        .replace("/", "|"),
                        page_file,
                    )
                )
    return names_files


async def process_file(
    knowledge_base: str, name_file: Tuple[str, str], force: bool = False
):
    useless_files = [f.replace("__.", "/") for f in os.listdir(IO_CONFIG.useless_dir)]

    name, file = name_file
    summary_dir = os.path.join(IO_CONFIG.summaries_dir, knowledge_base)
    os.makedirs(summary_dir, exist_ok=True)
    summary_file_path = os.path.join(summary_dir, name + ".md")
    if os.path.exists(summary_file_path) and not force:
        logger.info(f"Skipping file {name}...")
        return

    if summary_file_path in useless_files:
        logger.info(f"Skipping prev useless file {name}...")
        return

    logger.info(f"Processing file {name}...")
    with open(file, "r") as f:
        file_content = f.read()

    agent_response = await get_summarizer_response(file_content, name)

    if not agent_response.useful:
        useless_file = os.path.join(
            IO_CONFIG.useless_dir, summary_file_path.replace("/", "__.")
        )
        logger.info(f"Useless file {useless_file}...")
        with open(useless_file, "w") as f:
            f.write("")
        return

    with open(summary_file_path, "w") as f:
        f.write(agent_response.long_markdown_summary)

    r = Resource(
        knowledge_base=knowledge_base,
        identifier=name,
        summary_file_path=summary_file_path,
        short_description=agent_response.short_description,
    )
    r.upsert_resource()


async def process_all_files(knowledge_base: str, force: bool = False):
    files = get_all_files_for_processing(knowledge_base)
    files_per_batch = 20
    n_batches = math.ceil(len(files) / files_per_batch)
    batches = [files[i::n_batches] for i in range(n_batches)]
    assert sum(len(batch) for batch in batches) == len(files)
    for batch in batches:
        await asyncio.gather(
            *[process_file(knowledge_base, file, force) for file in batch]
        )


def run_parser(knowledge_base: str, force: bool = False):
    asyncio.run(process_all_files(knowledge_base, force))


if __name__ == "__main__":
    db_init()
    setup_stdout_logging()
    run_parser("zed_docs")
    run_parser("agno_docs")
    run_parser("ash_docs")
    run_parser("ash_docs_authentication")
    run_parser("ash_docs_json")
    run_parser("ash_docs_postgres")
    run_parser("ecto_docs")
    run_parser("phoenix_docs")
    run_parser("live_view_docs")
    run_parser("fly_docs")
    run_parser("fastapi_docs")
