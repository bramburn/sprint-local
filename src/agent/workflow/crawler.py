import asyncio
import logging
from typing import List, TypedDict, Union
from typing_extensions import Annotated

from crawl4ai import AsyncWebCrawler
from duckduckgo_search import DDGS
from langchain.output_parsers import RetryOutputParser, PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, field_validator
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages

from src.llm.ollama import get_ollama


# -------------------------------
# Define the Pydantic search query model
# -------------------------------
class SearchQuery(BaseModel):
    query: str = Field(
        description="The generated search query", min_length=5, max_length=200
    )
    intent: str = Field(default="", description="Intent of the query")

    @field_validator("query")
    def validate_query(cls, v):
        words = v.lower().split()
        forbidden_words = {"the", "a", "an", "and", "or", "in", "of", "to"}
        meaningful_words = [word for word in words if word not in forbidden_words]
        if len(meaningful_words) < 1:
            raise ValueError("Query must contain meaningful keywords")
        return v


# -------------------------------
# Define a Pydantic model to capture structured output for subqueries
# -------------------------------
class SubqueriesOutput(BaseModel):
    subqueries: List[SearchQuery]


# -------------------------------
# Define the CrawlerState using TypedDict with annotated messages
# -------------------------------
class CrawlerState(TypedDict, total=False):
    messages: Annotated[List[Union[HumanMessage, AIMessage]], add_messages]
    subqueries: List[SearchQuery]
    urls: List[str]
    markdown_contents: List[str]
    analysis: str
    summary: str
    code_example: str


# -------------------------------
# Global LLM instance (using LangChain's OllamaLLM for example)
# -------------------------------
llm = get_ollama(model="qwen2.5:latest", temperature=0.7)

# (For more robust output parsing, we set up a RetryOutputParser with structured output.)
base_parser = PydanticOutputParser(pydantic_object=SubqueriesOutput)
retry_parser = RetryOutputParser.from_llm(parser=base_parser, llm=llm, max_retries=2)


# -------------------------------
# Node 1: Generate Subqueries from a general SWE query
# -------------------------------
def generate_subqueries_node(state: CrawlerState) -> CrawlerState:
    """
    Uses LLM (via LangChain) to generate a list of detailed subqueries based on
    a general software engineering question. The output (one query per line) is parsed
    using a Pydantic model (with retry mechanism if needed).
    """
    question = state["messages"][-1].content
    format_instructions = retry_parser.get_format_instructions()

    # Escape curly braces in format instructions
    format_instructions = format_instructions.replace("{", "{{").replace("}", "}}")

    # Using ChatPromptTemplate for structured prompt generation
    template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful AI assistant."),
            (
                "human",
                f"Generate 5 detailed subqueries for researching the following software engineering topic: {question}."
                "For example include queries such as documentation, tutorials, best practices, etc.",
            ),
            ("system", format_instructions),
        ]
    )

    prompt_text = template.invoke({})
    response = llm.invoke(prompt_text)
    try:
        # Use parse_with_prompt instead of parse
        structured_output = retry_parser.parse_with_prompt(
            completion=response, prompt_value=prompt_text
        )
        subqueries = structured_output.subqueries
        state["subqueries"] = subqueries
        logging.info(f"Generated {len(subqueries)} subqueries using structured output.")
    except Exception as e:
        logging.error(f"Failed to parse subqueries using RetryOutputParser: {e}")
        state["subqueries"] = []
    return state


# -------------------------------
# Node 2: Execute DuckDuckGo search using generated subqueries
# -------------------------------
def duckduckgo_search_node(state: CrawlerState) -> CrawlerState:
    """
    Uses the duckduckgo-search Python module to look up each search query.
    Retrieves and aggregates unique URLs from the search results.
    """
    urls = []
    for sq in state.get("subqueries", []):
        try:
            with DDGS(timeout=10) as ddgs:
                results = list(ddgs.text(sq.query, max_results=5))
            for result in results:
                href = result.get("href")
                if href:
                    urls.append(href)
        except Exception as e:
            logging.warning(f"Search failed for query '{sq.query}': {e}")
    # Remove duplicate URLs.
    state["urls"] = list(set(urls))
    logging.info(f"Collected {len(state['urls'])} unique URLs from search.")
    return state


# -------------------------------
# Node 3: Crawl each URL and extract Markdown content using Crawl4AI
# -------------------------------
async def crawl_markdown_node(state: CrawlerState) -> CrawlerState:
    """
    Uses Crawl4AI's AsyncWebCrawler to fetch each URL and convert its content into Markdown.
    """
    markdown_contents = []
    urls = state.get("urls", [])
    async with AsyncWebCrawler(
        browser_config={"headless": True, "timeout": 30, "block_resources": True}
    ) as crawler:
        for url in urls:
            try:
                result = await crawler.arun(url=url)
                if result.markdown:
                    markdown_contents.append(result.markdown)
            except Exception as e:
                logging.warning(f"Error crawling {url}: {e}")
    state["markdown_contents"] = markdown_contents
    logging.info(f"Crawled {len(markdown_contents)} pages successfully.")
    return state


# -------------------------------
# Node 4: Analyze the Markdown content for relevant information
# -------------------------------
def analyze_contents_node(state: CrawlerState) -> CrawlerState:
    """
    Aggregates all Markdown content and uses the LLM to analyze it for key points,
    technical insights, common practices, or embedded example code.
    """
    combined_content = "\n".join(state.get("markdown_contents", []))

    # Using ChatPromptTemplate for structured prompt generation
    template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an expert in software engineering."),
            (
                "human",
                f"Analyze the following content for relevant software engineering information based on the user's query. "
                f"Summarize key technical concepts, common practices, and any sample code snippets."
                "Focus on the user's query: {SearchQuery}",
            ),
            ("system", "Content:\n{combined_content}\n\nSummary:"),
        ]
    )

    chain = template | llm
    SearchQuery = state["messages"][-1].content
    combined_content = "\n".join(state.get("markdown_contents", []))
    analysis = chain.invoke(
        {"combined_content": combined_content, "SearchQuery": SearchQuery}
    )
    state["analysis"] = analysis
    logging.info("Analysis from content completed.")
    return state


# -------------------------------
# Node 5: Generate a Final Summary from the Analysis
# -------------------------------
def generate_summary_node(state: CrawlerState) -> CrawlerState:
    """
    Uses the LLM to create a concise summary from the analysis.
    """
    analysis = state.get("analysis", "")

    # Using ChatPromptTemplate for structured prompt generation
    template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a summarization expert."),
            (
                "human",
                f"Based on the following analysis, generate a concise summary with key points and actionable insights "
                f"for a software engineering query."
                "The summary should help answer the user's query. user's query: {SearchQuery}"
                "information about our resesarch is here : {markdown_contents}",
            ),
            ("system", "Analysis:\n{analysis}\n\nSummary:"),
        ]
    )
    chain = template | llm
    SearchQuery = state["messages"][-1].content
    markdown_contents = "\n\n".join(state.get("markdown_contents", []))
    summary = chain.invoke(
        {
            "analysis": analysis,
            "SearchQuery": SearchQuery,
            "markdown_contents": markdown_contents,
        }
    )
    state["summary"] = summary
    logging.info("Final summary generated.")
    # Append the summary as an AI message to the conversation history
    state["messages"] = add_messages(state["messages"], [AIMessage(content=summary)])
    return state


# -------------------------------
# Node 6: Generate an Example Code Usage Based on the Summary
# -------------------------------
def generate_code_example_node(state: CrawlerState) -> CrawlerState:
    """
    Uses the LLM to generate an example code snippet that demonstrates how to implement or use the obtained concepts.
    """
    summary = state.get("summary", "")

    # Using ChatPromptTemplate for structured prompt generation
    template = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a code generation assistant."),
            (
                "human",
                f"Based on the following summary, generate a sample and self-contained example code snippet "
                f"that illustrates the discussed software engineering concepts. Include clear comments."
                "The code example should help answer the user's query. user's query: {SearchQuery}"
                "information about our resesarch is here : {markdown_contents}",
            ),
            ("system", "Summary:\n{summary}\n\nExample Code:"),
        ]
    )
    SearchQuery = state["messages"][-1].content
    markdown_contents = "\n\n".join(state.get("markdown_contents", []))
    chain = template | llm
    code_example = chain.invoke(
        {
            "summary": summary,
            "SearchQuery": SearchQuery,
            "markdown_contents": markdown_contents,
        }
    )
    state["code_example"] = code_example
    logging.info("Example code snippet generated.")
    # Append the code example as an AI message to the conversation history
    state["messages"] = add_messages(
        state["messages"], [AIMessage(content=code_example)]
    )
    return state


# -------------------------------
# Build the LangGraph workflow
# -------------------------------
def build_workflow():
    graph = StateGraph(CrawlerState)
    # Define nodes in the pipeline
    graph.add_node("generate_subqueries", generate_subqueries_node)
    graph.add_node("duckduckgo_search", duckduckgo_search_node)
    graph.add_node("crawl_markdown", crawl_markdown_node)  # Async node
    graph.add_node("analyze_contents", analyze_contents_node)
    graph.add_node("generate_summary", generate_summary_node)
    graph.add_node("generate_code_example", generate_code_example_node)

    # Wire up the edges between nodes
    graph.add_edge(START, "generate_subqueries")
    graph.add_edge("generate_subqueries", "duckduckgo_search")
    graph.add_edge("duckduckgo_search", "crawl_markdown")
    graph.add_edge("crawl_markdown", "analyze_contents")
    graph.add_edge("analyze_contents", "generate_summary")
    graph.add_edge("generate_summary", "generate_code_example")
    graph.add_edge("generate_code_example", END)

    return graph.compile()


# -------------------------------
# Main entry point to run the workflow
# -------------------------------
async def main():
    # Initial state: the user's SWE query is provided here.
    state: CrawlerState = {
        "messages": [
            HumanMessage(
                content="How do I implement dependency injection in Python using best practices?"
            )
        ]
    }
    workflow = build_workflow()
    final_state = await workflow.ainvoke(state)

    print("Final Summary:")
    print(final_state.get("summary"))
    print("\nAnalysis:")
    print(final_state.get("analysis"))
    print("\nOriginal User Query:")
    print(final_state["messages"][-1].content)
    print("\nGenerated Example Code:")
    print(final_state.get("code_example"))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
