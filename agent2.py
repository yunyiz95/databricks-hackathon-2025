import os
import langchain
import pandas as pd
import json
from openai import OpenAI
from databricks.sdk import WorkspaceClient
import mlflow
import asyncio
from typing import Optional
from databricks_langchain import ChatDatabricks
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
mlflow.openai.autolog()

instructions = """
"You are \"Nimble-Maps Assistant\", an advanced location intelligence assistant powered by Nimble's data retrieval technology.",
        "You have direct access to these Nimble-powered tools:",
        "• nimble_google_maps_search - For finding places based on search queries using Nimble's advanced search capabilities",
        "• nimble_google_maps_reviews - For fetching reviews using Nimble's comprehensive data extraction",
        "• nimble_google_maps_place - For filter the place based on the place id given",
        "CAPABILITIES:",
        "1. Find any type of location using Nimble's advanced search technology",
        "2. Search within specific geographic areas with precision",
        "3. Collect and analyze reviews for places through Nimble's data extraction",
        "4. Provide detailed location information (addresses, hours, ratings, etc.)",
        "",
        "RESPONSE FORMAT:",
        "• Provide clear, conversational updates throughout the process",
        "• When collecting multiple locations, organize them logically",
        "• ALWAYS collect at least 5 reviews for each location you find",
        "• For reviews, include ratings, dates, and text content",
        "• Present summary statistics when appropriate (avg rating, review count, etc.)",
        "• End with a conclusion that highlights key findings and offers next steps",
        "",
        "REVIEW COLLECTION PROCESS:",
        "• For every place found, ALWAYS use nimble_google_maps_reviews to fetch reviews",
        "• Before fetching reviews, tell the user which place you're collecting reviews for",
        "• Include the place_id parameter from the search results",
        "• Process at least the first page of reviews for each location",
        "• Extract reviewer name, rating, date, and review text",
        "• Mention that the reviews were retrieved using Nimble's technology"
"""

# Langchain example from https://docs.databricks.com/aws/en/notebooks/source/generative-ai/langgraph-tool-calling-agent.html
from databricks_langchain import (
    ChatDatabricks,
    UCFunctionToolkit,
    VectorSearchRetrieverTool,
)

# TODO: Replace with your model serving endpoint
LLM_ENDPOINT_NAME = "databricks-claude-sonnet-4"
llm = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)

from langchain_nimble import NimbleSearchRetriever

api_key = ''
# links = ['https://maps.google.com/']
retriever = NimbleSearchRetriever(k=3, 
                                  api_key=api_key,
                                  # search_engine='google_maps_search' # Not Avaialble
                                #   links = links
                                  )

                                  # Nimble MCP with Langchain
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

query="Recommend me top 3 brunch within 10 miles of 28226, filter for pregnancy safe or with safest food score."
# f"Search within place_id_list {place_id_list} provided and see if there is a restaurant"
# Recommend me top 3 brunch within 10 miles of 28226, filter for pregnancy safe or with safest food score."

MCP_URL = "https://mcp.nimbleway.com/sse"

# nimble_google_maps_search
client = MultiServerMCPClient({
    "nimble": {
        "url": MCP_URL,
        "transport": "sse",
        "headers": {"Authorization": f"Basic {api_key}"}
    }
})

# tools = await client.get_tools()

# Global placeholder
_agent_cache: Optional[create_react_agent] = None

async def load_agent():
    global _agent_cache
    if _agent_cache is None:
        # Load all available MCP tools
        tools = await client.get_tools()
        _agent_cache = create_react_agent(llm, 
                           tools = tools, 
                           prompt = instructions,
                           )
    return _agent_cache



# # Run the agent with the query
# print(f"Searching for information about: {query}")
# agent_response = await agent.ainvoke({
#     "messages": f"Find information about {query} and provide a concise summary."
# })

# print(agent_response)
