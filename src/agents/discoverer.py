from agno.agent import Agent  # type: ignore
from agno.models.google.gemini import Gemini
from env import GEMINI_API_KEY
from src.models.knowledge import DiscoveryOutput, KnowledgeBase, Resource
import os


def get_discoverer_response(knowledge_base: str, query: str) -> str:
    knowledge_base_exists = KnowledgeBase.knowledge_base_exists(knowledge_base)
    if not knowledge_base_exists:
        return "Knowledge base does not exist."

    resources = Resource.get_resources_by_knowledge_base(knowledge_base)
    resource_string = "\n".join([resource.context_string() for resource in resources])

    agent = Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=GEMINI_API_KEY),
        description="You are a archivist that specializes in finding relevant information from a corpus of technical documentation.",
        instructions=[
            "A user asks you to retrieve relevant information - the user specifies their request as follows:",
            query,
            "It is your job to find relevant resources to help inform the user's query.",
            "You must look through the list of summaries of resources below and select the most relevant ones.",
            "The full resource will then be retrieved and provided to the user.",
            "You may select up to 5 resources and must select at least one.",
            "The list of summaries of the resources is provided below:",
            "-------RESOURCE LIST START-------",
            resource_string,
            "-------RESOURCE LIST END-------",
            "Remember, you need to return the file paths of the resources you think will best inform the user's query.",
            "You must return the full resource_file_path for the resource you select.",
            "Here is the query again: ",
            query,
            "Since you have an overview of which resources are available, you can also optionally provide",
            "any additional comments where you think having overview information will help the user's query.",
            "Only provide additional comments if you think they will help the user's query.",
            "You are by no means obligated to provide additional comments. If there are no additional comments, simply return an empty string.",
        ],
        structured_outputs=True,
        response_model=DiscoveryOutput,
        markdown=True,
    )

    response = agent.run("Execute your instructions", retries=3)

    result: DiscoveryOutput = response.content  # type: ignore

    if not isinstance(result, DiscoveryOutput):
        return "Error retrieving resources"

    return_string = "Here is some extra information that might help inform your responses. Use them as you see fit\n"
    return_string += "----------------------------------------------------------\n"
    for file in result.resource_file_paths:
        if os.path.exists(file):
            with open(file, "r") as f:
                content = f.read()
                return_string += f"File: {file.split('/')[-1]}\nContent:\n{content}\n\n"
    return_string += "----------------------------------------------------------\n"

    if result.additional_comments != "":
        return_string += f"Additional Comments: {result.additional_comments}\n\n"

    return return_string
