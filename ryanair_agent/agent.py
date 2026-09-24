
import os
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from .tools import CheapestPerDayTool, AnalyzeTool, PlotTool

SYSTEM_PROMPT = (
    "Sei un agente che monitora prezzi voli Ryanair in modo etico e conforme. "
    "Usa i tool per raccogliere dati, analizzarli e generare grafici. "
    "Spiega le metriche e l'incertezza quando dai consigli."
)

def build_agent(model: str = None):
    model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model, temperature=0.2)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])
    tools = [CheapestPerDayTool, AnalyzeTool, PlotTool]
    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

if __name__ == "__main__":
    agent = build_agent()
    res = agent.invoke({"input": "Raccogli i prezzi BGY-CTA per 2026-12-19→2026-12-23 e poi analizza 2026-12-21."})
    print(res["output"]) 
