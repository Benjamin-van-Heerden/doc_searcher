from mcp.server.fastmcp import FastMCP
import multiprocessing as mp

from scripts.db_init import db_init

mcp = FastMCP("Technical Documentation Search")


@mcp.prompt()
def create_knowledge_base(tag: str):
    return "this"


@mcp.prompt()
def search_documentation(tag_and_query: str):
    tag, query = tag_and_query.split(":")
    return "this"


@mcp.prompt()
def list_knowledge_bases():
    return "this"


@mcp.prompt()
def delete_knowledge_base(tag: str):
    return "this"


if __name__ == "__main__":
    db_init()
    mcp.run()
