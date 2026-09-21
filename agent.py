import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate


def normalize_content(raw):
    if raw is None:
        return ""

    if isinstance(raw, str):
        return raw

    if isinstance(raw, list):
        parts = []
        for item in raw:
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        return "\n".join(parts)

    if isinstance(raw, dict):
        return json.dumps(raw, ensure_ascii=False, indent=2)

    return str(raw)


## GET LLM
def get_llm(model_name: str = "gemini-3.5-flash", temperature: float = 0.7):
    api_key = os.getenv("GEMINI_API_KEY")
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature, api_key=api_key)
    return llm


## RESEARCH AGENT
RESEARCH_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a research agent. Given a blog topic and audience, produce a clear research outline with 5-7 key points the blog should cover. Focus on important keywords, tags, suggested angles, or hooks. Be concise using bullet points."""),
    ("user", "Topic: {topic}\nAudience: {audience}\n{revision_hints}\nWrite the research outline now.")
])

def research_agent(llm, topic: str, audience: str, feedback: str = "") -> str:
    revision_hints = f"The human provided this feedback on previous research - please address it: {feedback}"
    if not feedback:
        revision_hints = "This is your first attempt."

    chain = RESEARCH_PROMPT | llm
    res = chain.invoke({
        "topic": topic,
        "audience": audience,
        "revision_hints": revision_hints
    })

    return normalize_content(res.content)


## WRITER AGENT
WRITER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert content writer. Given a research outline, topic, and audience, write a compelling, well-structured blog post draft. Use engaging headings and smooth transitions."""),
    ("user", "Topic: {topic}\nAudience: {audience}\nResearch Notes:\n{research}\n{revision_hints}\nWrite the blog draft now.")
])

def writer_agent(llm, topic: str, audience: str, research: str, feedback: str = "") -> str:
    revision_hints = f"The human provided this feedback on previous drafts - please address it: {feedback}"
    if not feedback:
        revision_hints = "This is your first attempt."

    chain = WRITER_PROMPT | llm
    res = chain.invoke({
        "topic": topic,
        "audience": audience,
        "research": research,
        "revision_hints": revision_hints
    })

    return normalize_content(res.content)


## EDITOR AGENT
EDITOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a professional editor. Review the blog draft for clarity, tone, flow, grammar, and engagement. Polish it into a final publication-ready piece."""),
    ("user", "Topic: {topic}\nDraft:\n{draft}\nProvide the final polished blog post now.")
])

def editor_agent(llm, topic: str, draft: str) -> str:
    chain = EDITOR_PROMPT | llm
    res = chain.invoke({
        "topic": topic,
        "draft": draft
    })

    return normalize_content(res.content)