# databricks-hackathon-2025

# 🤖 PregnancyPal: AI Life Assistant for Pregnant Women

**PregnancyPal** is a LangGraph-powered AI agent built to support pregnant women in finding personalized, safe, and accessible places—like brunch spots, clinics, or shops—based on their daily needs.

It combines natural language understanding with real-time data from **Nimble** (for maps and reviews) and **Bright Data** (for venue intelligence). The result: structured recommendations from free-form queries.

---

## 🧠 What This Does

- Parses user input like:
  > "I'm 33 weeks pregnant. I have a doctor appointment at 10am, then I want to find a healthy brunch nearby."

- Uses a **LangGraph pipeline**:
  1. **Agent 1**: Extracts structured intent (time, place type, restrictions)
  2. **Agent 2**: Searches places via Nimble and summarizes them in Markdown

- Returns an **AI-generated Markdown report** with:
  - 📍 Top 3 venue recommendations
  - 🛡️ Pregnancy-safe features
  - ⭐ Review highlights
  - 🗺️ Address, price range, and links

---

## 🛠️ How to Run

### 1. Invoke the Agent with a User Query

```python
query = "brunch near 28226 with pregnancy-safe food"
agent_response = await agent.ainvoke({
    "messages": f"Find information about {query} and provide a concise summary."
})
