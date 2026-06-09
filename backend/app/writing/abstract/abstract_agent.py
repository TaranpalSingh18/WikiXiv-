from app.main import LiveResearchResponse
from langchain_groq import ChatGroq
from writeup import Writeup
from dotenv import load_dotenv
load_dotenv()
import os

groq_api_key = os.getenv("GROQ_API_KEY")


def create_abstract(state: Writeup, context: str = LiveResearchResponse["report"]) -> Writeup:

    llm = ChatGroq(api_key= groq_api_key, model="meta-llama/llama-4-scout-17b-16e-instruct")
    prompt = f"""
You are a research abstract writing agent, and you just need the problem context and gap to just write up the abstract for my research paper. Make sure you use reseach terminologies, and return abstract only. I dont want people to know you're an AI in disguise of a human
"""
    
    abstract = llm.invoke(prompt)
    abstract_content = abstract.content

    if abstract_content is "":
        state["abstract"] = "Not extracted"
        return state
    
    abstract_content = abstract_content.strip()

    state["abstract"] = abstract_content

    return state





    

    



