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

class TaskItem(BaseModel):
    task_id: str = Field(description="Unique task identifier, e.g., T1, T2, etc.")
    description: str = Field(description="Clear, actionable, atomic developer description of the task.")
    category: str = Field(description="Category of the task: frontend, backend, database, api, or other.")
    depends_on: List[str] = Field(default=[], description="List of task_ids that this task depends on.")

class TaskBreakdownSchema(BaseModel):
    tasks: List[TaskItem] = Field(description="List of broken down actionable tasks with dependencies.")

class TaskBreakdownAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.0):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
        
        self.parser = JsonOutputParser(pydantic_object=TaskBreakdownSchema)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a Task Breakdown Agent in an AI-powered project management system.\n"
                "Your task is to take structured project requirements (JSON input) and convert them into clear, actionable development tasks.\n\n"
                "Instructions:\n"
                "1. Analyze the input requirements carefully.\n"
                "2. Break down each requirement into atomic, developer-friendly tasks (e.g. frontend design, backend logic, DB schema creation, api endpoint logic).\n"
                "3. Map tasks to categories: frontend, backend, database, api, or other.\n"
                "4. Maintain a logical dependency structure by populating 'depends_on' list with preceding task IDs.\n"
                "5. Do NOT hallucinate features or make assumptions not mentioned in the input requirements.\n\n"
                "Format instructions:\n{format_instructions}"
            )),
            ("user", "Input requirements:\n{requirements_input}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    def generate_tasks(self, requirements_json: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes structured requirements and generates atomic actionable tasks in JSON format.
        """
        if isinstance(requirements_json, dict):
            requirements_input = json.dumps(requirements_json, indent=2)
        elif isinstance(requirements_json, str):
            requirements_input = requirements_json.strip()
        else:
            return {"error": "Invalid requirements input format. Must be a dict or a JSON string.", "tasks": []}

        if not requirements_input:
            return {"error": "Requirements input is empty.", "tasks": []}
            
        try:
            result = self.chain.invoke({
                "requirements_input": requirements_input,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            return {
                "error": f"Failed to generate tasks: {str(e)}",
                "tasks": []
            }

# Example usage:
if __name__ == "__main__":
    agent = TaskBreakdownAgent()
    sample_requirements = {
        "project_goal": "Develop a doctor's appointment application that allows users to search for doctors by specialty and schedule bookings.",
        "user_types": [
            "Patient",
            "Doctor"
        ],
        "features": [
            "Search doctors by specialty",
            "Schedule bookings"
        ],
        "constraints": [
            "Patients are restricted to booking at most 2 appointments per day",
            "Use PostgreSQL as the database",
            "Complete the project in 3 weeks"
        ],
        "risks": [
            "Performance risk if website loading time is slow"
        ],
        "missing_information": []
    }
    result = agent.generate_tasks(sample_requirements)
    print(json.dumps(result, indent=2))
