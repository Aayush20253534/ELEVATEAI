import os
import json
import asyncio
from typing import Annotated, List, Dict, Any, TypedDict
from langchain_groq import ChatGroq
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

model = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3 , api_key=os.getenv("GROQ_API_KEY"))
web_search_tool = TavilySearchResults(k=3)



