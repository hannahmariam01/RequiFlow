import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

class RequirementsSchema(BaseModel):
    project_goal: str = Field(description="The core business goal extracted from the input text.")
    user_types: List[str] = Field(description="List of user roles or actors identified in the input.")
    features: List[str] = Field(description="List of all functional features extracted from the input.")
    constraints: List[str] = Field(description="List of technical, business, or timeline constraints.")
    risks: List[str] = Field(description="List of identified risks or ambiguities.")
    missing_information: List[str] = Field(description="List of missing, unclear, or unspecified areas in the input requirements.")

class RequirementUnderstandingAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.0):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
        
        self.parser = JsonOutputParser(pydantic_object=RequirementsSchema)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are the Requirement Intelligence Engine of RequiFlow.\n"
                "Your role is to convert raw user input into structured software requirements.\n\n"
                "Instructions:\n"
                "1. Extract the core business goal.\n"
                "2. Identify all user roles (actors).\n"
                "3. Identify all features (functional requirements).\n"
                "4. Identify constraints (technical, business, timeline).\n"
                "5. Identify risks.\n"
                "6. Identify missing or unclear areas (add to missing_information if unclear).\n\n"
                "Rules:\n"
                "- Do NOT hallucinate features.\n"
                "- Be concise but complete.\n\n"
                "Format instructions:\n{format_instructions}"
            )),
            ("user", "Input requirement text:\n{input_text}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    def analyze_requirements(self, input_text: str) -> Dict[str, Any]:
        """
        Analyzes raw requirements text and returns a structured JSON dictionary.
        """
        if not input_text or not isinstance(input_text, str) or not input_text.strip():
            return {
                "error": "Input text must be a non-empty string.",
                "project_goal": "",
                "user_types": [],
                "features": [],
                "constraints": [],
                "risks": [],
                "missing_information": []
            }
            
        try:
            result = self.chain.invoke({
                "input_text": input_text,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            return {
                "error": f"Failed to process requirements: {str(e)}",
                "project_goal": "",
                "user_types": [],
                "features": [],
                "constraints": [],
                "risks": [],
                "missing_information": []
            }

# Example usage:
if __name__ == "__main__":
    agent = RequirementUnderstandingAgent()
    sample_input = (
        "We want to build a doctors appointment application. Users must be able to search "
        "doctors by specialty and schedule bookings. The website must load in less than 1.5 seconds. "
        "Patients are restricted to booking at most 2 appointments per day. We must use PostgreSQL "
        "and complete the project in 3 weeks."
    )
    result = agent.analyze_requirements(sample_input)
    print(json.dumps(result, indent=2))
