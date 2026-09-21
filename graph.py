from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from state import BlogState
from agent import get_llm, research_agent, writer_agent, editor_agent

MAX_REVISION = 3

## 1. RESEARCHER NODE
def researcher_node(state: BlogState):
    llm = get_llm()
    research_data = research_agent(
        llm=llm,
        topic=state.topic,
        audience=state.audience,
        feedback=state.research_feedback
    )
    state.research = research_data
    return state


## 2. HUMAN REVIEW (RESEARCH) NODE
def human_review_research_node(state: BlogState):
    decision = interrupt({
        "stage": "research_review",
        "research": state.research,
        "instruction": "Reply with 'approve' to proceed to writing, or provide feedback/changes to revise the research."
    })
    
    if isinstance(decision, dict):
        action = decision.get("action", "approve")
        feedback = decision.get("feedback", "")
    else:
        text = str(decision).strip()
        action = "approve" if text.lower() in ["approve", "ok", "yes", ""] else "revise"
        feedback = "" if action == "approve" else text
        
    state.research_feedback = feedback
    state.revision_count += 1
    return state


def should_revise_research(state: BlogState):
    if not state.research_feedback or state.revision_count >= MAX_REVISION:
        return "writer"
    return "researcher"


## 3. WRITER NODE
def writer_node(state: BlogState):
    llm = get_llm()
    draft_data = writer_agent(
        llm=llm,
        topic=state.topic,
        audience=state.audience,
        research=state.research,
        feedback=state.draft_feedback  # Matches state schema
    )
    state.draft = draft_data
    return state


## 4. HUMAN REVIEW (WRITER/DRAFT) NODE
def human_review_writer_node(state: BlogState):
    decision = interrupt({
        "stage": "writer_review",
        "draft": state.draft,
        "instruction": "Reply with 'approve' to send to editor, or provide feedback/changes to revise the draft."
    })
    
    if isinstance(decision, dict):
        action = decision.get("action", "approve")
        feedback = decision.get("feedback", "")
    else:
        text = str(decision).strip()
        action = "approve" if text.lower() in ["approve", "ok", "yes", ""] else "revise"
        feedback = "" if action == "approve" else text
        
    state.draft_feedback = feedback  # Matches state schema
    state.revision_count += 1
    return state


def should_revise_writer(state: BlogState):
    if not state.draft_feedback or state.revision_count >= MAX_REVISION:  # Matches state schema
        return "editor"
    return "writer"


## 5. EDITOR NODE (Takes only topic and draft)
def editor_node(state: BlogState):
    llm = get_llm()
    final_blog_content = editor_agent(
        llm=llm,
        topic=state.topic,
        draft=state.draft
    )
    state.final_blog = final_blog_content  # Matches state schema
    return state


## 6. BUILD GRAPH FUNCTION
def build_blog_graph():
    workflow = StateGraph(BlogState)

    # Add Nodes
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("human_review_research", human_review_research_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("human_review_writer", human_review_writer_node)
    workflow.add_node("editor", editor_node)

    # Add Edges & Conditional Routing
    workflow.add_edge(START, "researcher")
    workflow.add_edge("researcher", "human_review_research")

    workflow.add_conditional_edges(
        "human_review_research",
        should_revise_research,
        {
            "researcher": "researcher",
            "writer": "writer"
        }
    )

    workflow.add_edge("writer", "human_review_writer")

    workflow.add_conditional_edges(
        "human_review_writer",
        should_revise_writer,
        {
            "writer": "writer",
            "editor": "editor"
        }
    )

    workflow.add_edge("editor", END)

    # Compile Graph with Memory Checkpointer for interrupts
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)
    
    return graph