# Databricks notebook source
# %python
# import importlib

# def install_if_missing(package):
#     try:
#         importlib.import_module(package)
#     except ImportError:
#         %pip install -U -qqq {package}

# install_if_missing('langchain_core')
# install_if_missing('langchain_databricks')
# install_if_missing('langchain_community')

# dbutils.library.restartPython()

# COMMAND ----------

# import importlib

# def install_if_missing(package):
#     try:
#         importlib.import_module(package)
#     except ImportError:
#         %pip install -U -qqq {package}

# install_if_missing('langchain-nimble')
# install_if_missing('langchain-openai')
# install_if_missing('mlflow')
# install_if_missing('backoff')
# install_if_missing('databricks-openai')
# install_if_missing('databricks-agents')
# install_if_missing('uv')
# install_if_missing('databricks-langchain')
# install_if_missing('langgraph==0.3.4')
# install_if_missing('langchain_mcp_adapters')

# dbutils.library.restartPython()

# COMMAND ----------

# # 1) Declare a widget to receive the question
# dbutils.widgets.text("question", "", "Question")
# question = dbutils.widgets.get("question")

# print(f"▶️ Received question: {question}")

# COMMAND ----------

# # Langchain example from https://docs.databricks.com/aws/en/notebooks/source/generative-ai/langgraph-tool-calling-agent.html
# from databricks_langchain import (
#     ChatDatabricks,
#     UCFunctionToolkit,
#     VectorSearchRetrieverTool,
# )

# # TODO: Replace with your model serving endpoint
# LLM_ENDPOINT_NAME = "databricks-claude-sonnet-4"
# llm = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)

# COMMAND ----------

# from langchain_nimble import NimbleSearchRetriever

# api_key = 'YWNjb3VudC1uaWFnYXJhX2JvdHRsaW5nXzQ2b3Z2NS1waXBlbGluZS1uaW1ibGVhcGk6OWQ0MWw1NUNFQzJD'
# # links = ['https://maps.google.com/']
# retriever = NimbleSearchRetriever(k=3, 
#                                   api_key=api_key,
#                                   # search_engine='google_maps_search' # Not Avaialble
#                                 #   links = links
#                                   )

# COMMAND ----------

# instructions = """
# "You are \"Nimble-Maps Assistant\", an advanced location intelligence assistant powered by Nimble's data retrieval technology.",
#         "You have direct access to these Nimble-powered tools:",
#         "• nimble_google_maps_search - For finding places based on search queries using Nimble's advanced search capabilities",
#         "• nimble_google_maps_reviews - For fetching reviews using Nimble's comprehensive data extraction",
#         "• nimble_google_maps_place - For filter the place based on the place id given",
#         "CAPABILITIES:",
#         "1. Find any type of location using Nimble's advanced search technology",
#         "2. Search within specific geographic areas with precision",
#         "3. Collect and analyze reviews for places through Nimble's data extraction",
#         "4. Provide detailed location information (addresses, hours, ratings, etc.)",
#         "",
#         "RESPONSE FORMAT:",
#         "• Provide clear, conversational updates throughout the process",
#         "• When collecting multiple locations, organize them logically",
#         "• ALWAYS collect at least 5 reviews for each location you find",
#         "• For reviews, include ratings, dates, and text content",
#         "• Present summary statistics when appropriate (avg rating, review count, etc.)",
#         "• End with a conclusion that highlights key findings and offers next steps",
#         "",
#         "REVIEW COLLECTION PROCESS:",
#         "• For every place found, ALWAYS use nimble_google_maps_reviews to fetch reviews",
#         "• Before fetching reviews, tell the user which place you're collecting reviews for",
#         "• Include the place_id parameter from the search results",
#         "• Process at least the first page of reviews for each location",
#         "• Extract reviewer name, rating, date, and review text",
#         "• Mention that the reviews were retrieved using Nimble's technology"
# """

# COMMAND ----------

# # Nimble MCP with Langchain
# from langchain_mcp_adapters.client import MultiServerMCPClient
# from langgraph.prebuilt import create_react_agent

# # query="Hotels in Charlotte NC with accessible facilities"
# query = question
# # query = "Which ecommerce platform have 24 pack of half litre water?"

# MCP_URL = "https://mcp.nimbleway.com/sse"

# # nimble_google_maps_search
# client = MultiServerMCPClient({
#     "nimble": {
#         "url": MCP_URL,
#         "transport": "sse",
#         "headers": {"Authorization": f"Basic {api_key}"}
#     }
# })
# # Load all available MCP tools
# tools = await client.get_tools()

# agent = create_react_agent(llm, tools = tools, prompt = instructions)

# # Run the agent with the query
# print(f"Searching for information about: {query}")
# agent_response = await agent.ainvoke({
#     "messages": f"Find information about {query} and provide a concise summary."
# })

# print(agent_response)

# COMMAND ----------

agent_response = """AIMessage(content='Perfect! I\'ve collected comprehensive information about brunch restaurants near 28226 and gathered detailed reviews for the top pregnancy-safe options. Let me provide you with my findings and recommendations.

## **Top 3 Pregnancy-Safe Brunch Recommendations Near 28226**

Based on my analysis using Nimble\'s advanced location intelligence and review collection technology, here are the safest brunch options for pregnancy within 10 miles of 28226:

### **🥇 #1: First Watch (Providence Farms Location)**
**Address:** 6311 Providence Farm Ln Suite 100, Charlotte, NC 28226  
**Rating:** 4.5 stars (1,900 reviews) | **Price:** $10-20  

**Why It\'s Pregnancy-Safe:**
- **Health-focused chain** specializing in fresh, organic ingredients
- **Extensive healthy options** including organic dishes and fresh salads
- **Vegetarian and vegan options** available
- **Great tea selection** (caffeine-free options)
- **Family-friendly atmosphere**

**Recent Review Highlights:**
- "Food was perfect, as always" - Gabriela H.
- "Great seasonal specials... always well done" - Angela Anagho
- Avocado toast and fresh ingredients consistently praised

---

### **🥈 #2: KID CASHEW (Elizabeth Location)**
**Address:** 1608 East Blvd, Charlotte, NC 28203  
**Rating:** 4.6 stars (3,672 reviews) | **Price:** $10-20  

**Why It\'s Pregnancy-Safe:**
- **Mediterranean cuisine** with emphasis on fresh, healthy ingredients
- **Extensive vegan and vegetarian options**
- **Organic and healthy dishes** prominently featured
- **Gluten-free restaurant** with safe preparation practices
- **Family-friendly** (name says it all!)

**Recent Review Highlights:**
- "Great for kids... quinoa salad was delicious" - Nyador Elwell III
- "Fresh and flavorful... high-quality ingredients" - Danijela Pope
- "Grilled chicken, tender and moist... ingredients are so fresh" - Snailo Morphesis
- "Great options for selective diets" - Shaneka R.

---

### **🥉 #3: Ruby Sunshine (West Bland St Location)**
**Address:** 332 W Bland St, Charlotte, NC 28203  
**Rating:** 4.7 stars (4,725 reviews) | **Price:** $10-20  

**Why It\'s Pregnancy-Safe:**
- **Vegetarian and vegan options** available
- **Fresh, made-from-scratch approach**
- **Gluten-free options** for dietary restrictions
- **Family-friendly** and **LGBTQ+ friendly** environment
- **Great coffee** (can request decaf)

**Recent Review Highlights:**
- "Gluten free options... my celiac friend rarely gets to eat yummy things" - Stacie Baldwin
- "Everything was amazing... didn\'t even need syrup" - Queen H.
- "Great food, great service and great prices" - David Mack

---

## **Summary & Safety Features**

**Key Pregnancy-Safe Features Found:**
✅ **Fresh, organic ingredients** (First Watch, KID CASHEW)  
✅ **Extensive vegetarian/vegan options** (all three locations)  
✅ **Gluten-free accommodations** (Ruby Sunshine, KID CASHEW)  
✅ **Family-friendly atmospheres** (all locations)  
✅ **High food safety standards** (evidenced by consistent positive reviews)  
✅ **Healthy preparation methods** (grilled vs. fried options available)  

**Average Ratings:** All three restaurants maintain 4.5+ star ratings with thousands of reviews, indicating consistent food safety and quality standards.

**Next Steps:** I\'d recommend calling ahead to discuss any specific dietary restrictions or pregnancy-related food safety concerns. All three restaurants have demonstrated flexibility in accommodating special dietary needs.

*This analysis was powered by Nimble\'s comprehensive location intelligence and review collection technology, ensuring you have the most current and detailed information for making safe dining choices during pregnancy.*', additional_kwargs={}, response_metadata={'model': 'us.anthropic.claude-sonnet-4-20250514-v1:0', 'usage': {'prompt_tokens': 95320, 'completion_tokens': 985, 'total_tokens': 96305}, 'object': 'chat.completion', 'id': 'msg_bdrk_01K4DGm1dtXUPk5VKpgWBgnB', 'created': 1749489527, 'model_name': 'us.anthropic.claude-sonnet-4-20250514-v1:0'}, id='run--c411a2f9-2684-40f8-a5a9-ced8d70a5645-0')]"""

# COMMAND ----------

%pip install openai

# COMMAND ----------

from openai import OpenAI
import os

# How to get your Databricks token: https://docs.databricks.com/en/dev-tools/auth/pat.html
# DATABRICKS_TOKEN = os.environ.get('DATABRICKS_TOKEN')
# Alternatively in a Databricks notebook you can use this:
DATABRICKS_TOKEN = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

client = OpenAI(
    api_key=DATABRICKS_TOKEN,
    base_url="https://dbc-4ff3d9fe-2240.cloud.databricks.com/serving-endpoints"
)

# Use agent_response as context to generate summaries
response = client.chat.completions.create(
    model="databricks-claude-sonnet-4",
    messages=[
        {
            "role": "user",
            "content": f"Based on the following recommendations: {agent_response}, provide a concise summary of each."
        }
    ]
)

print(response.choices[0].message.content)

# COMMAND ----------

# summary_content = response.choices[0].message.content
# # if too big, trim or save out to /dbfs/tmp/…
# dbutils.notebook.exit(summary_content[:4_000_000])


# COMMAND ----------

# 2) Return the response back to the caller
result = response.choices[0].message.content
dbutils.notebook.exit(result)


# COMMAND ----------

# # … your agent logic …

# from pyspark.dbutils import DBUtils
# dbutils = DBUtils(spark)

# # Get the LLM response
# summary_content = response.choices[0].message.content

# # Build a small JSON object and exit
# import json
# dbutils.notebook.exit(json.dumps({"answer": summary_content}))
