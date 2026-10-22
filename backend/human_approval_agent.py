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

class KeyPoints(BaseModel):
    goal: str = Field(description="Core project goal, translated into non-technical language.")
    features: List[str] = Field(description="List of features in non-technical terms.")
    constraints: List[str] = Field(description="List of constraints in non-technical terms.")
    risks: List[str] = Field(description="List of risks in non-technical terms.")

class ApprovalSchema(BaseModel):
    summary: str = Field(description="Clear, non-technical, simple explanation of the project.")
    key_points: KeyPoints = Field(description="Key details organized by goal, features, constraints, and risks.")
    questions_for_human: List[str] = Field(description="List of questions for the human, converted from missing_information. If missing_information is empty or missing, this must be an empty array [].")
    action_required: str = Field(description="Must be strictly the literal string 'Approve / Reject / Suggest Changes'.")
    approval_status: str = Field(description="Must be strictly the literal string 'pending'.")

class HumanApprovalAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.0):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
        
        self.parser = JsonOutputParser(pydantic_object=ApprovalSchema)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are the Human-in-the-Loop Approval Agent of RequiFlow.\n"
                "Your role is to act as the bridge between automated system outputs and human decision-making. "
                "You convert structured technical requirements into a clear, simple, human-friendly presentation and request approval.\n\n"
                "Instructions:\n"
                "1. Transform the input requirements JSON into a clear, non-technical, simple summary.\n"
                "2. Extract and present key points (Goal, Features, Constraints, Risks) using clear, non-technical language.\n"
                "3. If 'missing_information' exists in the input JSON, convert those items into clear, user-friendly questions for the human. If it doesn't exist or is empty, 'questions_for_human' must be empty [].\n"
                "4. Always set 'action_required' to the literal string 'Approve / Reject / Suggest Changes'.\n"
                "5. Always set 'approval_status' to the literal string 'pending'.\n"
                "6. Do NOT make decisions on behalf of the human. Do NOT output raw input JSON. Do NOT hallucinate or add any new data not present in the input.\n\n"
                "Format instructions:\n{format_instructions}"
            )),
            ("user", "Input Requirements JSON:\n{requirements_input}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    def prepare_approval_request(self, requirements_json: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Converts technical requirements into a human-friendly approval request presentation.
        """
        if isinstance(requirements_json, dict):
            requirements_input = json.dumps(requirements_json, indent=2)
        elif isinstance(requirements_json, str):
            requirements_input = requirements_json.strip()
        else:
            return {"error": "Invalid requirements input format. Must be a dict or a JSON string."}

        if not requirements_input:
            return {"error": "Requirements input is empty."}
            
        try:
            result = self.chain.invoke({
                "requirements_input": requirements_input,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            return {
                "error": f"Failed to generate approval request: {str(e)}",
                "summary": "Error generating summary",
                "key_points": {
                    "goal": "",
                    "features": [],
                    "constraints": [],
                    "risks": []
                },
                "questions_for_human": [],
                "action_required": "Approve / Reject / Suggest Changes",
                "approval_status": "pending"
            }

# Example usage:
if __name__ == "__main__":
    agent = HumanApprovalAgent()
    
    print("--- Test Case 1: Refined Requirements (No missing info) ---")
    refined_reqs = {
        "project_goal": "Build a doctor's appointment application",
        "user_types": [
            "Patients",
            "Doctors"
        ],
        "features": [
            "Search doctors by specialty",
            "Schedule bookings",
            "Display appointment schedule",
            "User authentication and authorization",
            "Payment processing for appointments"
        ],
        "constraints": [
            "Website load time must be less than 1.5 seconds",
            "Use PostgreSQL database",
            "Complete project in 3 weeks",
            "Patients can book at most 2 appointments per day",
            "Patients must pay a $50 booking fee before confirmation"
        ],
        "risks": [
            "Meeting the 3-week project deadline",
            "Ensuring the website loads within the 1.5-second time frame",
            "Integrating Stripe payment processing successfully"
        ],
        "missing_information": []
    }
    
    result_1 = agent.prepare_approval_request(refined_reqs)
    print(json.dumps(result_1, indent=2))
    
    print("\n--- Test Case 2: Incomplete Requirements (With missing info) ---")
    incomplete_reqs = {
        "project_goal": "Build a doctor's appointment application",
        "user_types": [
            "Patients",
            "Doctors"
        ],
        "features": [
            "Search doctors by specialty",
            "Schedule bookings"
        ],
        "constraints": [
            "Use PostgreSQL database",
            "Complete project in 3 weeks"
        ],
        "risks": [
            "Meeting the 3-week project deadline"
        ],
        "missing_information": [
            "User authentication and authorization details",
            "Payment processing for appointments"
        ]
    }
    
    result_2 = agent.prepare_approval_request(incomplete_reqs)
    print(json.dumps(result_2, indent=2))
