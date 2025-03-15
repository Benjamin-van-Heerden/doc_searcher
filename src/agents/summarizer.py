from agno.agent import Agent  # type: ignore
from agno.models.google.gemini import Gemini
from env import GEMINI_API_KEY
from src.models.knowledge import LLMResource


async def get_summarizer_response(file_content: str, name: str) -> LLMResource:
    agent = Agent(
        model=Gemini(id="gemini-2.0-flash", api_key=GEMINI_API_KEY),
        description="""You are a technical documentation expert that understands complex documentation
        and converts it to structured data.""",
        instructions=[
            "Povided below is a markdown document that was converted from a technical documentation web page.",
            "Your task is to convert the document to structured data.",
            "Ignore any strange repeated text or things like nevbars, headers or footers"
            "Provide a short summary of what is contained in the document,",
            "a long form cleaned markdown version of the document, and crucially, whether the document is useful",
            "When determining whether the document is useful, consider the following factors:",
            "1. Is the core content of the document very short? - if it is, it is not useful",
            "Reason through it like this: could many of these have been combined into a single document? - if so, it is probably not useful",
            "2. Does the document convey a major process or concept?",
            "If e.g. a 'Person' has many 'Jobs', a document that shows how a Person can be created with",
            "a specific Job, that is not useful (the major concept is the Person - the Job is essentially an argument for the Person)",
            "This is really important, if no major concept or process is conveyed, the document is not useful",
            "3. Suppose you were to include the document in a task description, would it add notable value?"
            "If the answer to this question is something like 'no' or 'not really' or 'kind of' or even 'maybe' - the document is not useful",
            "For determining whether a document is useful, you should be more reckless than cautious",
            "4. Could you imagine that this information is available elsewhere in the rest of the documentation?",
            "If you think it is, the document is not useful",
            "We are trying to distill the essence of a large corpus of technical documentation and we want to discard as much as possible.",
            "Any extraneous information must be removed, so only mark it as useful if you deem it absolutely essential and necessary",
            "NB: if there is any indication that the document is from a different version of an api or sdk, it is not useful",
            "Changelogs and really long seemingly repetitive information is also not useful",
            "Here is the document content:",
            "---------------------",
            file_content,
            "---------------------",
            f"The document originates from {name} (remember to look for version information)",
        ],
        structured_outputs=True,
        response_model=LLMResource,
        markdown=True,
    )

    response = await agent.arun("Execute your instructions", retries=3)
    result: LLMResource = response.content

    if not isinstance(result, LLMResource):
        raise ValueError("Invalid response")

    return result
