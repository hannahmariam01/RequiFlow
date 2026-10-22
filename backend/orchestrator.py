import os
import json
import asyncio
from typing import Dict, Any, Union

# Import agents
from requirement_understanding_agent import RequirementUnderstandingAgent
from clarification_agent import ClarificationAgent
from requirement_refinement_agent import RequirementRefinementAgent
from architecture_agent import ArchitectureAgent
from task_breakdown_agent import TaskBreakdownAgent
from flowchart_agent import FlowchartAgent

# Instantiate agents
understanding_agent = RequirementUnderstandingAgent()
clarification_agent = ClarificationAgent()
refinement_agent = RequirementRefinementAgent()
architecture_agent = ArchitectureAgent()
task_breakdown_agent = TaskBreakdownAgent()
flowchart_agent = FlowchartAgent()

async def run_pipeline(
    input_text: str = None,
    original_requirements: Dict[str, Any] = None,
    user_answers: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Orchestrates the entire agent pipeline using async/await.
    
    1. If user_answers are provided:
       -> Refine requirements using RequirementRefinementAgent.
       Otherwise:
       -> Extract requirements using RequirementUnderstandingAgent from input_text.
       
    2. Check if missing_information exists:
       -> Run ClarificationAgent to generate clarification questions and RETURN them (halts flow).
       
    3. Run ArchitectureAgent to design system architecture based on requirements.
    
    4. Run TaskBreakdownAgent based on combined requirements and architecture design.
    
    5. Run FlowchartAgent to construct a Mermaid flowchart of the architecture and tasks.
    
    6. Return the final unified JSON dictionary.
    """
    # 1. Run Understanding or Refinement
    if user_answers:
        if not original_requirements:
            return {"error": "Missing original_requirements when user_answers are provided."}
        try:
            requirements = await asyncio.to_thread(
                refinement_agent.refine_requirements, original_requirements, user_answers
            )
        except Exception as e:
            return {"error": f"Error in RequirementRefinementAgent: {str(e)}"}
    else:
        if not input_text:
            return {"error": "Missing input_text or user_answers."}
        try:
            requirements = await asyncio.to_thread(
                understanding_agent.analyze_requirements, input_text
            )
        except Exception as e:
            return {"error": f"Error in RequirementUnderstandingAgent: {str(e)}"}

    if "error" in requirements:
        return {"error": requirements["error"]}

    # 2. Check for missing information
    missing_info = requirements.get("missing_information", [])
    if missing_info and len(missing_info) > 0:
        try:
            clarification = await asyncio.to_thread(
                clarification_agent.generate_questions, requirements
            )
            return clarification
        except Exception as e:
            return {"error": f"Error in ClarificationAgent: {str(e)}"}

    # 3. Design Architecture
    try:
        architecture = await asyncio.to_thread(
            architecture_agent.design_architecture, requirements
        )
    except Exception as e:
        return {"error": f"Error in ArchitectureAgent: {str(e)}"}

    if "error" in architecture:
        return {"error": architecture["error"]}

    # 4. Generate Task Breakdown
    try:
        combined_input = {**requirements, "architecture": architecture}
        task_breakdown = await asyncio.to_thread(
            task_breakdown_agent.generate_tasks, combined_input
        )
    except Exception as e:
        return {"error": f"Error in TaskBreakdownAgent: {str(e)}"}

    if "error" in task_breakdown:
        return {"error": task_breakdown["error"]}

    tasks = task_breakdown.get("tasks", [])

    # 5. Generate Flowchart
    try:
        flowchart_input = {
            "architecture": architecture,
            "tasks": tasks
        }
        flowchart_result = await asyncio.to_thread(
            flowchart_agent.generate_flowchart, flowchart_input
        )
    except Exception as e:
        return {"error": f"Error in FlowchartAgent: {str(e)}"}

    if "error" in flowchart_result:
        return {"error": flowchart_result["error"]}

    flowchart = flowchart_result.get("flowchart", "")

    # 6. Return Final Output
    return {
        "requirements": requirements,
        "architecture": architecture,
        "tasks": tasks,
        "flowchart": flowchart
    }

# Example usage to verify orchestrator flow
if __name__ == "__main__":
    import sys
    # Support executing via JSON CLI payload
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        try:
            payload = json.loads(sys.argv[2])
            
            async def run_cli():
                result = await run_pipeline(
                    input_text=payload.get("input_text"),
                    original_requirements=payload.get("original_requirements"),
                    user_answers=payload.get("user_answers")
                )
                print(json.dumps(result))
                
            asyncio.run(run_cli())
        except Exception as e:
            print(json.dumps({"error": f"CLI execution error: {str(e)}"}))
    else:
        async def main():
            print("=== Test Case 1: Requirements Needing Clarification ===")
            incomplete_input = (
                "We want to build a clinic scheduling application, but we haven't decided "
                "what database to use or how many appointments a user can book."
            )
            
            result_1 = await run_pipeline(input_text=incomplete_input)
            print("Pipeline output:")
            print(json.dumps(result_1, indent=2))
            
            print("\n=== Test Case 2: Complete Requirements (Refining Test Case 1 answers) ===")
            # Use a mock original requirement with missing info
            original_reqs = {
                "project_goal": "Build a clinic scheduling application.",
                "user_types": ["Patient", "Doctor"],
                "features": ["Schedule clinic slots"],
                "constraints": ["Complete in 3 weeks"],
                "risks": [],
                "missing_information": [
                    "User authentication details",
                    "Database choice",
                    "Appointment limits"
                ]
            }
            mock_answers = {
                "answers": [
                    {
                        "question_id": 1,
                        "answer": "Users authenticate using basic email and password."
                    },
                    {
                        "question_id": 2,
                        "answer": "Use PostgreSQL as the database."
                    },
                    {
                        "question_id": 3,
                        "answer": "Patients are limited to 2 bookings per day."
                    }
                ]
            }
            
            result_2 = await run_pipeline(
                original_requirements=original_reqs,
                user_answers=mock_answers
            )
            print("Pipeline output:")
            print(json.dumps(result_2, indent=2))

        asyncio.run(main())
