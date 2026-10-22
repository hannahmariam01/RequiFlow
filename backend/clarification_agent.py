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

class ClarificationQuestion(BaseModel):
    id: int = Field(description="Unique question identifier starting from 1.")
    category: str = Field(description="Category of the question: Feature | User | Technical | Business")
    question: str = Field(description="Specific, actionable, high-value clarification question.")

class ClarificationSchema(BaseModel):
    questions: List[ClarificationQuestion] = Field(description="List of clarification questions.")

class ClarificationAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.0):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
        
        self.parser = JsonOutputParser(pydantic_object=ClarificationSchema)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are the Clarification Engine of RequiFlow.\n"
                "Your role is to analyze structured requirement inputs and generate high-value, intelligent clarification questions based on incomplete information and identified risks.\n\n"
                "STRICT RULE:\n"
                "Do NOT introduce, assume, or ask about any new features, requirements, technologies, or concepts (e.g., scalability, post-launch maintenance, KPIs) that are not explicitly mentioned in the input.\n"
                "Base all questions ONLY on:\n"
                "- The list of 'missing_information'\n"
                "- The list of 'risks'\n"
                "- Explicitly mentioned 'features'\n"
                "Every question must map directly back to a specific item from one of these lists.\n\n"
                "Instructions:\n"
                "1. Analyze the 'missing_information' list to detect gaps in functionality, roles, technical systems, or business constraints.\n"
                "2. Analyze the 'risks' list to identify uncertain, ambiguous, or critical areas that need clarification.\n"
                "3. Generate high-value, specific, and actionable clarification questions. Do NOT ask generic, obvious, or vague questions (e.g., 'Can you clarify this?').\n"
                "4. Avoid unnecessary yes/no questions. Questions should prompt descriptive, actionable answers.\n"
                "5. Ensure there are no duplicate questions, and generate a maximum of 10 questions in total.\n"
                "6. Categorize each question into one of the following exact categories:\n"
                "   - Feature: Functionality gaps, user interface behaviors, or workflow rules.\n"
                "   - User: Roles, permissions, access levels, or actor details.\n"
                "   - Technical: System integration, performance benchmarks, database, or architectural decisions.\n"
                "   - Business: Project goals, business priorities, roadmap, scope boundaries, or legal/compliance requirements.\n\n"
                "Format instructions:\n{format_instructions}"
            )),
            ("user", "Input requirements:\n{requirements_input}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    def generate_questions(self, requirement_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates clarification questions based on requirement JSON.
        """
        if isinstance(requirement_json, dict):
            requirements_input = json.dumps(requirement_json, indent=2)
        elif isinstance(requirement_json, str):
            requirements_input = requirement_json.strip()
        else:
            return {"error": "Invalid requirements input format. Must be a dict or a JSON string.", "questions": []}

        if not requirements_input:
            return {"error": "Requirements input is empty.", "questions": []}
            
        try:
            result = self.chain.invoke({
                "requirements_input": requirements_input,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            return {
                "error": f"Failed to generate clarification questions: {str(e)}",
                "questions": []
            }

# Example usage:
if __name__ == "__main__":
    agent = ClarificationAgent()
    sample_requirements = {
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
    result = agent.generate_questions(sample_requirements)
    print(json.dumps(result, indent=2))
