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

class ArchitectureSchema(BaseModel):
    frontend: str = Field(description="Selected frontend technology, framework, and basic structure.")
    backend: str = Field(description="Selected backend technology, framework, and runtime environment.")
    database: str = Field(description="Selected database engine, schema design, or setup choice.")
    services: List[str] = Field(description="List of auxiliary services (e.g. auth, cache, messaging queues, background tasks).")
    apis: List[str] = Field(description="Key API endpoints or communication protocols (e.g. REST API, WebSockets, GraphQL).")
    infrastructure: List[str] = Field(description="Hosting, deployment, CI/CD, or infrastructure components (e.g. AWS S3, Vercel, Docker).")
    architecture_notes: List[str] = Field(description="Clear, logical reasoning and justification for each choice, mapping directly to features or constraints.")

class ArchitectureAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.0):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
        
        self.parser = JsonOutputParser(pydantic_object=ArchitectureSchema)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a Senior System Architect.\n"
                "Your role is to analyze structured project requirements and design a simple, realistic, and scalable system architecture.\n\n"
                "STRICT RULES:\n"
                "1. Do NOT invent random, unnecessary, or speculative technologies (such as Kubernetes, Kafka, Microservices, Hadoop, Spark, etc.) unless specifically requested in the features or constraints. Keep it as simple, standard, and realistic as possible.\n"
                "2. Base all architectural decisions strictly on the provided requirements (project goal, features, user types, constraints).\n"
                "3. Clearly separate frontend, backend, database, services, APIs, and infrastructure.\n"
                "4. You must explain the reasoning behind your choices in the 'architecture_notes' section. Each note must justify why a technology or design choice was made, referencing specific features, user types, or constraints.\n\n"
                "Format instructions:\n{format_instructions}"
            )),
            ("user", "Input requirements:\n{requirements_input}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    def design_architecture(self, requirements: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Designs system architecture based on structured requirements input.
        """
        if isinstance(requirements, dict):
            requirements_input = json.dumps(requirements, indent=2)
        elif isinstance(requirements, str):
            requirements_input = requirements.strip()
        else:
            return {
                "error": "Invalid requirements input format. Must be a dict or a JSON string.",
                "frontend": "",
                "backend": "",
                "database": "",
                "services": [],
                "apis": [],
                "infrastructure": [],
                "architecture_notes": []
            }

        if not requirements_input:
            return {
                "error": "Requirements input is empty.",
                "frontend": "",
                "backend": "",
                "database": "",
                "services": [],
                "apis": [],
                "infrastructure": [],
                "architecture_notes": []
            }
            
        try:
            result = self.chain.invoke({
                "requirements_input": requirements_input,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            return {
                "error": f"Failed to design architecture: {str(e)}",
                "frontend": "",
                "backend": "",
                "database": "",
                "services": [],
                "apis": [],
                "infrastructure": [],
                "architecture_notes": []
            }

# Example usage:
if __name__ == "__main__":
    agent = ArchitectureAgent()
    sample_requirements = {
        "project_goal": "Develop a doctor's appointment application that allows users to search for doctors by specialty and schedule bookings.",
        "user_types": [
            "Patient",
            "Doctor"
        ],
        "features": [
            "Search doctors by specialty",
            "Schedule bookings",
            "Display appointment schedule"
        ],
        "constraints": [
            "Patients are restricted to booking at most 2 appointments per day",
            "Use PostgreSQL as the database",
            "Complete the project in 3 weeks",
            "Website load time must be less than 1.5 seconds"
        ]
    }
    result = agent.design_architecture(sample_requirements)
    print(json.dumps(result, indent=2))
