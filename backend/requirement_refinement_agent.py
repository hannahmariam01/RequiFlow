import os
import json
from typing import List, Dict, Any, Union
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

class RequirementRefinementAgent:
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
                "You are the Requirement Refinement Engine of RequiFlow.\n"
                "Your role is to update and refine structured project requirements based on user answers to clarification questions.\n\n"
                "Objective:\n"
                "Incorporate the new information from user answers to resolve ambiguities, specify details, update features, constraints, risks, and remove resolved missing items.\n\n"
                "Core Responsibilities:\n"
                "1. Merge new information into the existing project fields.\n"
                "2. Update 'user_types' if new roles or actors are identified in the answers.\n"
                "3. Add or refine 'features' based on user answers.\n"
                "4. Update 'constraints' if new or clarified limits/technologies/deadlines are provided.\n"
                "5. Reduce or modify 'risks' where the user answers resolve uncertainty. Add new risks only if answers introduce new ambiguities.\n"
                "6. Remove items from 'missing_information' when they are fully resolved by user answers, or refine them if only partially resolved.\n\n"
                "Critical Rules:\n"
                "- DO NOT remove valid existing features, user types, constraints, or goals that are not affected or resolved by the answers.\n"
                "- ONLY modify or add to fields when user answers provide concrete new information.\n"
                "- DO NOT hallucinate features, requirements, or constraints not explicitly mentioned in the original requirements or in the user's answers.\n"
                "- Ensure all list items are clean, concise, deduplicated, and logically consistent (no contradictions).\n\n"
                "Refinement Strategy:\n"
                "- Map each answer back to its original context (e.g. if an answer explains how doctor scheduling works, update 'features' or 'constraints' and remove 'Doctor availability and scheduling rules' from 'missing_information').\n\n"
                "Format instructions:\n{format_instructions}"
            )),
            ("user", "Original Requirements:\n{original_requirements}\n\nUser Answers:\n{user_answers}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    def refine_requirements(self, original: Dict[str, Any], answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intelligently refines requirements based on user answers.
        """
        # Validate inputs
        if not isinstance(original, dict) or not isinstance(answers, dict):
            return {"error": "Invalid input formats. Both 'original' and 'answers' must be dictionaries."}
            
        try:
            result = self.chain.invoke({
                "original_requirements": json.dumps(original, indent=2),
                "user_answers": json.dumps(answers, indent=2),
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            return {
                "error": f"Failed to refine requirements: {str(e)}",
                "project_goal": original.get("project_goal", ""),
                "user_types": original.get("user_types", []),
                "features": original.get("features", []),
                "constraints": original.get("constraints", []),
                "risks": original.get("risks", []),
                "missing_information": original.get("missing_information", [])
            }

# Example usage:
if __name__ == "__main__":
    agent = RequirementRefinementAgent()
    original_requirements = {
        "project_goal": "Build a doctor's appointment application",
        "user_types": [
            "Patients",
            "Doctors"
        ],
        "features": [
            "Search doctors by specialty",
            "Schedule bookings",
            "Display appointment schedule"
        ],
        "constraints": [
            "Website load time must be less than 1.5 seconds",
            "Use PostgreSQL database",
            "Complete project in 3 weeks",
            "Patients can book at most 2 appointments per day"
        ],
        "risks": [
            "Meeting the 3-week project deadline",
            "Ensuring the website loads within the 1.5-second time frame"
        ],
        "missing_information": [
            "User authentication and authorization details",
            "Payment processing for appointments",
            "Doctor availability and scheduling rules"
        ]
    }

    mock_answers = {
        "answers": [
            {
                "question_id": 1,
                "answer": "Patients will sign up and log in via email and password. Doctors will be authenticated using pre-configured corporate accounts. Only Doctors can view patient medical records."
            },
            {
                "question_id": 2,
                "answer": "Stripe will be integrated to handle payment processing for appointments. Users must pay a booking fee of $50 before confirmation."
            },
            {
                "question_id": 3,
                "answer": "Doctor availability will be defined by daily time slots (e.g., 9 AM - 5 PM). Doctors can mark slots as unavailable, and patients can select only open slots."
            }
        ]
    }

    result = agent.refine_requirements(original_requirements, mock_answers)
    print(json.dumps(result, indent=2))
