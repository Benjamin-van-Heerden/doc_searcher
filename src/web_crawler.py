import asyncio
import os
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlResult,
    CrawlerRunConfig,
)
from cfg import IO_CONFIG
import logging
from typing import List
from scripts.db_init import db_init
from src.models.knowledge import KnowledgeBase
import requests
import re
from typing import Tuple

from utils.loggers import setup_stdout_logging

logger = logging.getLogger(__name__)


def get_sitemap(base_url: str):
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    try:
        response = requests.get(sitemap_url)
        if response.status_code == 200:
            return response.text
        else:
            logger.warning(f"Failed to fetch sitemap from {sitemap_url}")
    except Exception as e:
        logger.error(f"Error fetching sitemap from {sitemap_url}: {e}")
    return None


def parse_sitemap_into_links(sitemap: str):
    return [
        r.replace("</loc>", "")
        for r in re.findall(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            sitemap,
        )
    ]


async def scrape_website(
    base_url: str,
    knowledge_base: str,
    max_depth: int = 3,
    redo: bool = False,
    ignored_tags: list[str] = [],
    alternative_seeds: List[str] = [],
) -> None:
    if not ignored_tags:
        ignored_tags = ["form", "nav", "footer"]

    base_name = urlparse(base_url).netloc  # Extract domain name
    output_dir = os.path.join(IO_CONFIG.docs_dir, knowledge_base)
    os.makedirs(output_dir, exist_ok=True)

    await _scrape_recursive(
        url=base_url,
        depth=0,
        output_dir=output_dir,
        max_depth=max_depth,
        base_url=base_url,
        redo=redo,
        ignored_tags=ignored_tags,
        visited_urls=set(),
    )

    for seed in alternative_seeds:
        await _scrape_recursive(
            url=seed,
            depth=0,
            output_dir=output_dir,
            max_depth=1,
            base_url=base_url,
            redo=redo,
            ignored_tags=ignored_tags,
            visited_urls=set(),
        )

    maybe_sitemap = get_sitemap(base_url)
    if maybe_sitemap:
        links = parse_sitemap_into_links(maybe_sitemap)
        for link in links:
            if link.startswith(base_url):
                await _scrape_recursive(
                    url=link,
                    depth=0,
                    output_dir=output_dir,
                    max_depth=0,
                    base_url=base_url,
                    redo=redo,
                    ignored_tags=ignored_tags,
                    visited_urls=set(),
                )


async def _scrape_recursive(
    url: str,
    depth: int,
    output_dir: str,
    max_depth: int,
    base_url: str,
    redo: bool,
    ignored_tags: list[str],
    visited_urls: set[str],
) -> None:
    if depth > max_depth or url in visited_urls:
        return

    page_dir = os.path.join(output_dir, *urlparse(url).path.strip("/").split("/"))
    output_file = os.path.join(page_dir, "page.md")

    if not redo and os.path.exists(output_file):
        logger.info(f"Already scraped {url} - depth {depth}")
        return

    visited_urls.add(url)

    browser_config = BrowserConfig(
        headless=True,
        viewport_width=1920,
        viewport_height=1080,
    )

    run_config_pre = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=200,
        wait_for="body",
    )
    run_config_post = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=200,
        wait_for="body",
        excluded_tags=["form", "nav", "footer", "header"] + ignored_tags,
    )

    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            pre_post = [
                crawler.arun(url, config=run_config_pre),
                crawler.arun(url, config=run_config_post),
            ]

            r: Tuple[CrawlResult, CrawlResult] = await asyncio.gather(*pre_post)  # type: ignore
            result_pre, result_post = r

            markdown = result_post.markdown

            if not markdown or "404" in markdown and len(markdown) < 500:
                logger.warning(f"{url} is empty or a 404.")
            else:
                os.makedirs(page_dir, exist_ok=True)
                with open(output_file, "w") as f:
                    f.write(markdown.strip())
                logger.info(f"Scraped {url} to {output_file}")

            # Extract and follow links
            soup = BeautifulSoup(result_pre.html, "html.parser")
            links = [
                urljoin(url, a.get("href")) for a in soup.find_all("a") if a.get("href")  # type: ignore
            ]
            valid_links = {
                link.split("#")[0]
                for link in links
                if link.startswith(base_url)
                and (
                    urlparse(link).path.endswith((".html", ".md"))
                    or urlparse(link).path.split("/")[-1].split(".")[0]
                    == urlparse(link).path.split("/")[-1]
                )
            }  # Only crawl links that start with base URL and end with .html or / or .md or has no extension (is not a file)

            for link in valid_links:
                await _scrape_recursive(
                    url=link,
                    depth=depth + 1,
                    output_dir=output_dir,
                    max_depth=max_depth,
                    base_url=base_url,
                    redo=redo,
                    ignored_tags=ignored_tags,
                    visited_urls=visited_urls,
                )

    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")


def run_scraper(
    base_url: str,
    knowledge_base: str,
    max_depth: int = 3,
    redo: bool = False,
    ignored_tags: List[str] = [],
    alternative_seeds: List[str] = [],
):
    use_base = base_url if base_url.endswith("/") else base_url + "/"
    KnowledgeBase.create_knowledge_base(knowledge_base, base_url)
    asyncio.run(
        scrape_website(
            base_url=use_base,
            knowledge_base=knowledge_base,
            max_depth=max_depth,
            redo=redo,
            ignored_tags=ignored_tags,
            alternative_seeds=alternative_seeds,
        )
    )


if __name__ == "__main__":
    db_init()
    setup_stdout_logging()
    run_scraper(
        base_url="https://zed.dev/docs/",
        knowledge_base="zed_docs",
        redo=False,
    )
    run_scraper(
        base_url="https://docs.agno.com/",
        alternative_seeds=[
            "https://docs.agno.com/examples/getting-started/custom-tools",
            "https://docs.agno.com/examples/concepts/multimodal/audio-sentiment-analysis",
            "https://docs.agno.com/examples/agents/finance-agent",
            "https://docs.agno.com/examples/workflows/blog-post-generator",
            "https://docs.agno.com/examples/concepts/rag/traditional-rag-pgvector",
            "https://docs.agno.com/examples/concepts/knowledge/arxiv-kb",
            "https://docs.agno.com/examples/concepts/memory/builtin-memory",
            "https://docs.agno.com/examples/concepts/teams/news-agency-team",
            "https://docs.agno.com/examples/concepts/async/basic",
            "https://docs.agno.com/examples/concepts/hybrid-search/lancedb",
            "https://docs.agno.com/examples/concepts/storage/dynamodb",
            "https://docs.agno.com/examples/concepts/tools/duckduckgo",
            "https://docs.agno.com/examples/concepts/vectordb/cassandra",
            "https://docs.agno.com/examples/concepts/embedders/azure-embedder",
            "https://docs.agno.com/examples/models/openai/basic",
        ],
        knowledge_base="agno_docs",
        redo=False,
    )
    run_scraper(
        base_url="https://hexdocs.pm/ash/",
        knowledge_base="ash_docs",
        redo=False,
    )
    run_scraper(
        base_url="https://hexdocs.pm/ash_phoenix/",
        knowledge_base="ash_docs_phoenix",
        redo=False,
    )
    run_scraper(
        base_url="https://hexdocs.pm/ash_postgres/",
        knowledge_base="ash_docs_postgres",
        redo=False,
    )
    run_scraper(
        base_url="https://hexdocs.pm/ash_authentication/",
        knowledge_base="ash_docs_authentication",
        redo=False,
    )
    run_scraper(
        base_url="https://hexdocs.pm/ash_json_api/",
        knowledge_base="ash_docs_json",
        redo=False,
    )
    run_scraper(
        base_url="https://hexdocs.pm/ecto/",
        knowledge_base="ecto_docs",
        redo=False,
    )
    run_scraper(
        base_url="https://hexdocs.pm/phoenix/",
        knowledge_base="phoenix_docs",
        redo=False,
    )
    run_scraper(
        base_url="https://hexdocs.pm/phoenix_live_view/",
        knowledge_base="live_view_docs",
        redo=False,
    )
