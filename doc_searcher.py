from mcp.server.fastmcp import FastMCP
import multiprocessing as mp
from src.agents.discoverer import get_discoverer_response
from src.models.knowledge import KnowledgeBase

from scripts.db_init import db_init

mcp = FastMCP("Technical Documentation Search")


@mcp.prompt()
def search_documentation(tag_and_query: str):
    tag, query = tag_and_query.split(":")
    return get_discoverer_response(tag, query)


@mcp.prompt()
def list_knowledge_bases():
    all_knowledge_bases = KnowledgeBase.get_knowledge_bases()
    return "\n".join(f"{kb.name}" for kb in all_knowledge_bases)


if __name__ == "__main__":
    db_init()
    mcp.run()
