from typing import Any, Generator, Optional, Sequence, Union

import mlflow
from databricks_langchain import (
    ChatDatabricks,
    VectorSearchRetrieverTool,
    DatabricksFunctionClient,
    UCFunctionToolkit,
    set_uc_function_client,
)
from langchain_core.language_models import LanguageModelLike
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt.tool_node import ToolNode
from mlflow.langchain.chat_agent_langgraph import ChatAgentState, ChatAgentToolNode
from mlflow.pyfunc import ChatAgent
from mlflow.types.agent import (
    ChatAgentChunk,
    ChatAgentMessage,
    ChatAgentResponse,
    ChatContext,
)

mlflow.langchain.autolog()

client = DatabricksFunctionClient()
set_uc_function_client(client)

############################################
# Define your LLM endpoint and system prompt
############################################
LLM_ENDPOINT_NAME = "databricks-claude-sonnet-4"
llm = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)

system_prompt = """You are an intelligent AI assistant to recommend best shop, restaurant, and other places for pregnant women to take care about their needs, health and mood. You will take the input from the user and generate an outline with
1. time requirement (e.g. after 13:00)
2. location requirement (e.g. within zipcode 28226, 5 miles within a certain address)
3. place type (e.g. restaurant, shop, medical center)
4. Other requirement (e.g. safe food choices for pregnant women; medical services specialized for pregnancy)
Based on the user input, I want the output to be a clear description such as "Recommend me top 3 brunch within 10 miles of 28226, filter for pregnancy safe or with safest food score."
"""

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

###############################################################################
## Define tools for your agent, enabling it to retrieve data or take actions
## beyond text generation
## To create and see usage examples of more tools, see
## https://docs.databricks.com/generative-ai/agent-framework/agent-tool.html
###############################################################################
tools = []

# You can use UDFs in Unity Catalog as agent tools
uc_tool_names = []
uc_toolkit = UCFunctionToolkit(function_names=uc_tool_names)
tools.extend(uc_toolkit.tools)


# # (Optional) Use Databricks vector search indexes as tools
# # See https://docs.databricks.com/generative-ai/agent-framework/unstructured-retrieval-tools.html
# # for details
#
# # TODO: Add vector search indexes as tools or delete this block
# vector_search_tools = [
#         VectorSearchRetrieverTool(
#         index_name="",
#         # filters="..."
#     )
# ]
# tools.extend(vector_search_tools)


#####################
## Define agent logic
#####################


def create_tool_calling_agent(
    model: LanguageModelLike,
    tools: Union[Sequence[BaseTool], ToolNode],
    system_prompt: Optional[str] = None,
) -> CompiledGraph:
    model = model.bind_tools(tools)

    # Define the function that determines which node to go to
    def should_continue(state: ChatAgentState):
        messages = state["messages"]
        last_message = messages[-1]
        # If there are function calls, continue. else, end
        if last_message.get("tool_calls"):
            return "continue"
        else:
            return "end"

    if system_prompt:
        preprocessor = RunnableLambda(
            lambda state: [{"role": "system", "content": system_prompt}]
            + state["messages"]
        )
    else:
        preprocessor = RunnableLambda(lambda state: state["messages"])
    model_runnable = preprocessor | model

    def call_model(
        state: ChatAgentState,
        config: RunnableConfig,
    ):
        response = model_runnable.invoke(state, config)

        return {"messages": [response]}

    workflow = StateGraph(ChatAgentState)

    workflow.add_node("agent", RunnableLambda(call_model))
    workflow.add_node("tools", ChatAgentToolNode(tools))

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()


class LangGraphChatAgent(ChatAgent):
    def __init__(self, agent: CompiledStateGraph):
        self.agent = agent

    def predict(
        self,
        messages: list[ChatAgentMessage],
        context: Optional[ChatContext] = None,
        custom_inputs: Optional[dict[str, Any]] = None,
    ) -> ChatAgentResponse:
        request = {"messages": self._convert_messages_to_dict(messages)}

        messages = []
        for event in self.agent.stream(request, stream_mode="updates"):
            for node_data in event.values():
                messages.extend(
                    ChatAgentMessage(**msg) for msg in node_data.get("messages", [])
                )
        return ChatAgentResponse(messages=messages)

    def predict_stream(
        self,
        messages: list[ChatAgentMessage],
        context: Optional[ChatContext] = None,
        custom_inputs: Optional[dict[str, Any]] = None,
    ) -> Generator[ChatAgentChunk, None, None]:
        request = {"messages": self._convert_messages_to_dict(messages)}
        for event in self.agent.stream(request, stream_mode="updates"):
            for node_data in event.values():
                yield from (
                    ChatAgentChunk(**{"delta": msg}) for msg in node_data["messages"]
                )

# Create the agent object, and specify it as the agent object to use when
# loading the agent back for inference via mlflow.models.set_model()
agent = create_tool_calling_agent(llm, tools, system_prompt)
AGENT = LangGraphChatAgent(agent)
mlflow.models.set_model(AGENT)
