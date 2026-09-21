from pydantic import BaseModel

class BlogState(BaseModel):

    ##User inputs
    topic:str=""
    audience:str=""
    
    ##Researcher outputs
    research:str=""
    research_feedback:str=""

    ##writer outputs
    draft:str=""
    draft_feedback:str=""

    ##Editor outputs
    final_blog:str=""

    #Metadata
    revision_count:int=0
