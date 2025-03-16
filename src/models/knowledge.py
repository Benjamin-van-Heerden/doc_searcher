from os import stat
from pydantic import BaseModel, Field
from typing import List
from src.utils.db_context import DBCursor


class KnowledgeBase(BaseModel):
    name: str
    url: str

    @staticmethod
    def db_init():
        with DBCursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    name TEXT PRIMARY KEY,
                    url TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def knowledge_base_exists(name: str) -> bool:
        with DBCursor() as cursor:
            cursor.execute(
                f"""
                SELECT EXISTS (
                    SELECT 1 FROM knowledge_bases WHERE name = :name
                );
                """,
                {"name": name},
            )
            return cursor.fetchone()[0]

    @staticmethod
    def create_knowledge_base(name: str, url: str):
        with DBCursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO knowledge_bases (name, url)
                VALUES (:name, :url)
                ON CONFLICT (name) DO NOTHING;
                """,
                {"name": name, "url": url},
            )

    @staticmethod
    def get_knowledge_bases() -> List["KnowledgeBase"]:
        with DBCursor() as cursor:
            cursor.execute(
                f"""
                SELECT * FROM knowledge_bases;
                """
            )
            return [KnowledgeBase(**row) for row in cursor.fetchall()]


class Resource(BaseModel):
    knowledge_base: str
    identifier: str
    summary_file_path: str
    short_description: str

    @staticmethod
    def db_init():
        with DBCursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS resources (
                    knowledge_base TEXT NOT NULL,
                    identifier TEXT NOT NULL,
                    summary_file_path TEXT NOT NULL,
                    short_description TEXT NOT NULL,
                    PRIMARY KEY (knowledge_base, identifier)
                );
                """
            )

    def context_string(self):
        return f"Resource(resource_file_path={self.summary_file_path}, summary={self.short_description})"

    @staticmethod
    def get_resources_by_knowledge_base(knowledge_base: str) -> List["Resource"]:
        with DBCursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM resources WHERE lower(knowledge_base) LIKE lower(:pattern);
                """,
                {"pattern": knowledge_base},
            )
            return [Resource(**row) for row in cursor.fetchall()]

    @staticmethod
    def get_resources_by_knowledge_base_all_subtree(
        knowledge_base: str,
    ) -> List["Resource"]:
        with DBCursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM resources WHERE lower(knowledge_base) LIKE lower(:pattern);
                """,
                {"pattern": f"{knowledge_base}%"},
            )
            return [Resource(**row) for row in cursor.fetchall()]

    def upsert_resource(self):
        with DBCursor() as cursor:
            cursor.execute(
                """
                INSERT INTO resources (knowledge_base, identifier, summary_file_path, short_description)
                VALUES (:knowledge_base, :identifier, :summary_file_path, :short_description)
                ON CONFLICT(knowledge_base, identifier) DO UPDATE SET
                    summary_file_path = excluded.summary_file_path,
                    short_description = excluded.short_description;
                """,
                self.__dict__,
            )

    @staticmethod
    def upsert_resources(rs: List["Resource"]):
        with DBCursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO resources (knowledge_base, identifier, summary_file_path, short_description)
                VALUES (:knowledge_base, :identifier, :summary_file_path, :short_description)
                ON CONFLICT(knowledge_base, identifier) DO UPDATE SET
                    summary_file_path = excluded.summary_file_path,
                    short_description = excluded.short_description;
                """,
                [r.__dict__ for r in rs],
            )


class LLMResource(BaseModel):
    short_description: str = Field(
        ...,
        description="""A short description of the resource, i.e. 'what is going on in the resource?', notable functions, classes, examples, etc.
        Keep it brief.
        """,
    )
    long_markdown_summary: str = Field(
        ...,
        description="""The data contained in the resource, cleaned up and shortened in markdown format.
        Any codeblocks or explanations of usage must be preserved, but things like navbars, headers, and footers can be removed - only the content is important.
        If it seems like information is being repeated, only keep one or two examples.
        If there is something really long and not apparently "useful to humans", it should be removed.
        """,
    )
    useful: bool = Field(
        ...,
        description="""A boolean indicating whether the resource is useful.
        Here you should err on the side of recklessness in the sense that
        we want to clear out as much unnecessary information as possible. E.g. if the document is short or it does not
        describe a major process or concept, it is considered not useful.
        """,
    )


class DiscoveryOutput(BaseModel):
    resource_file_paths: List[str] = Field(
        ...,
        description="A list of file paths to the summary files of the resources. Max of 5 files.",
    )
    additional_comments: str = Field(
        ...,
        description="Additional comments about the resources.",
    )
