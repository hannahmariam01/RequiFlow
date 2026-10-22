import os
import json
from typing import Dict, Any, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

class FlowchartSchema(BaseModel):
    flowchart: str = Field(description="Mermaid.js flowchart source code using 'graph TD' syntax, visualizing system flow from user to frontend, backend, database, services, and APIs.")

class FlowchartAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.0):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
        
        self.llm = ChatGroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
        
        self.parser = JsonOutputParser(pydantic_object=FlowchartSchema)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a system visualization expert.\n"
                "Your role is to take a system architecture design and broken-down development tasks, and generate a clean, readable flowchart in Mermaid.js format.\n\n"
                "STRICT RULES:\n"
                "1. The flowchart must use standard, correct Mermaid syntax (specifically 'graph TD').\n"
                "2. Show the logical and operational flow of the system starting from the User, leading to the Frontend, Backend, Database, and including any key Services and APIs defined in the input.\n"
                "3. Keep the diagram clean, structured, and easy to read. Do not create excessively complex connections or loops unless they represent real flows.\n"
                "4. Enclose node labels in quotes if they contain any special characters or spaces (e.g. Node1[\"Label (Info)\"]). Do NOT use HTML tags in node labels.\n"
                "5. STRICT RULE ON ARROWS WITH TEXT LABELS: Use the exact syntax: A -->|label| B  or  A -- label --> B. Do NOT use A -->|label|> B or A -->|label|> (the extra trailing > character is a syntax error in Mermaid).\n\n"
                "Format instructions:\n{format_instructions}"
            )),
            ("user", "Input data:\n{input_data}")
        ])
        
        self.chain = self.prompt | self.llm | self.parser

    def generate_flowchart(self, data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates a Mermaid.js flowchart based on input architecture and tasks data.
        """
        if isinstance(data, dict):
            input_data = json.dumps(data, indent=2)
        elif isinstance(data, str):
            input_data = data.strip()
        else:
            return {
                "error": "Invalid input format. Must be a dict or a JSON string.",
                "flowchart": ""
            }

        if not input_data:
            return {
                "error": "Input data is empty.",
                "flowchart": ""
            }
            
        try:
            result = self.chain.invoke({
                "input_data": input_data,
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            return {
                "error": f"Failed to generate flowchart: {str(e)}",
                "flowchart": ""
            }

# Example usage:
if __name__ == "__main__":
    agent = FlowchartAgent()
    sample_data = {
        "architecture": {
            "frontend": "React with Material-UI",
            "backend": "Node.js with Express.js",
            "database": "PostgreSQL database",
            "services": [
                "Authentication service",
                "Email service"
            ],
            "apis": [
                "REST API for searching doctors by specialty",
                "REST API for scheduling bookings"
            ],
            "infrastructure": [
                "AWS S3 for static assets",
                "Heroku for server deployment"
            ]
        },
        "tasks": [
            {
                "task_id": "T1",
                "description": "Design PostgreSQL database schema for doctors and appointments",
                "category": "database",
                "depends_on": []
            },
            {
                "task_id": "T2",
                "description": "Implement authentication endpoints (register/login)",
                "category": "api",
                "depends_on": ["T1"]
            },
            {
                "task_id": "T3",
                "description": "Implement doctor search and booking REST APIs",
                "category": "api",
                "depends_on": ["T2"]
            },
            {
                "task_id": "T4",
                "description": "Build doctor search frontend interface using React and Material-UI",
                "category": "frontend",
                "depends_on": ["T3"]
            }
        ]
    }
    result = agent.generate_flowchart(sample_data)
    print(json.dumps(result, indent=2))
