from src.models.knowledge import KnowledgeBase, Resource


def db_init():
    KnowledgeBase.db_init()
    Resource.db_init()
