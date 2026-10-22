import os
import json
from typing import List, Dict, Any, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_groq import ChatGroq

load_dotenv()

class UserStoryItemSchema(BaseModel):
    id: str = Field(description="Story ID, e.g., US-001, US-002, etc.")
    role: str = Field(description="The user role or actor, e.g., patient, customer, admin.")
    feature: str = Field(description="The action or capability, e.g., browse products by category.")
    benefit: str = Field(description="The business benefit or value, e.g., find items quickly.")
    text: str = Field(description="The full user story in standard format: 'As a [role], I want to [feature] so that [benefit]'. Avoid HTML tag wrap around role here.")
    acceptance_criteria: List[str] = Field(description="List of 3-5 specific, testable acceptance criteria points for developer validation.")
    priority: str = Field(description="Priority: 'high', 'medium', or 'low'.")
    story_points: int = Field(description="Estimation of story complexity using story points: 1, 2, 3, 5, or 8.")
    epic: str = Field(description="Epic/Category of the story, e.g., Authentication, Catalog, Admin, Payments.")

class UserStoriesSchema(BaseModel):
    user_stories: List[UserStoryItemSchema] = Field(description="List of detailed user stories generated based on the project requirements.")

class UserStoryAgent:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile", temperature: float = 0.2):
        api_key = os.getenv("GROQ_API_KEY")
        self.use_llm = True
        if not api_key:
            print("WARNING: GROQ_API_KEY environment variable is not set. Falling back to mock generator.")
            self.use_llm = False
            return
            
        try:
            self.llm = ChatGroq(
                groq_api_key=api_key,
                model_name=model_name,
                temperature=temperature
            )
            self.parser = JsonOutputParser(pydantic_object=UserStoriesSchema)
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are an expert Senior Product Owner and Business Analyst.\n"
                    "Your role is to analyze a software project's goal, technical architecture, and tasks, "
                    "and generate a list of high-quality, professional, and detailed user stories.\n\n"
                    "STRICT RULES:\n"
                    "1. Each user story must represent a clear slice of user-facing value.\n"
                    "2. Each story must have detailed Acceptance Criteria (3-5 points) which are clear, testable, and specific to the project.\n"
                    "3. Prioritize stories based on business value ('high', 'medium', 'low').\n"
                    "4. Estimate story points (1, 2, 3, 5, or 8) representing complexity and effort.\n"
                    "5. Categorize stories into Epics matching the main components of the software.\n\n"
                    "Format instructions:\n{format_instructions}"
                )),
                ("user", "Input project context:\n{project_context}")
            ])
            self.chain = self.prompt | self.llm | self.parser
        except Exception as e:
            print(f"WARNING: Failed to initialize ChatGroq: {str(e)}. Falling back to mock generator.")
            self.use_llm = False

    def generate_user_stories(self, project_context: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if not self.use_llm:
            return self.generate_mock_user_stories(project_context)

        if isinstance(project_context, dict):
            context_str = json.dumps(project_context, indent=2)
        else:
            context_str = str(project_context).strip()
            
        try:
            result = self.chain.invoke({
                "project_context": context_str,
                "format_instructions": self.parser.get_format_instructions()
            })
            # Ensure return has user_stories key
            if "user_stories" not in result:
                raise ValueError("Output format missing 'user_stories' key")
            return result
        except Exception as e:
            print(f"Error in UserStoryAgent via Groq API: {str(e)}. Falling back to mock generator.")
            return self.generate_mock_user_stories(project_context)

    def generate_mock_user_stories(self, project_context: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(project_context, dict):
            req_str = project_context.get("project_title", "") + " " + json.dumps(project_context.get("requirements", {}))
        else:
            req_str = str(project_context)
            
        req_lower = req_str.lower()
        stories = []
        
        # Check for doctor/healthcare
        if "doctor" in req_lower or "health" in req_lower or "clinic" in req_lower or "patient" in req_lower:
            stories.extend([
                {
                    "id": "US-001",
                    "role": "patient",
                    "epic": "Doctor Search",
                    "feature": "search for doctors by specialty and availability",
                    "benefit": "find a suitable doctor for my symptoms",
                    "text": "As a patient, I want to search for doctors by specialty and availability, so that I can find a suitable doctor for my symptoms.",
                    "acceptance_criteria": [
                        "User can filter doctors by specialty (e.g. Cardiology, Pediatrics).",
                        "Availability slots for each doctor must be displayed in a calendar grid.",
                        "Search results should load in less than 1 second."
                    ],
                    "priority": "high",
                    "story_points": 3
                },
                {
                    "id": "US-002",
                    "role": "patient",
                    "epic": "Appointment Booking",
                    "feature": "book a consultation slot and pay the fee online",
                    "benefit": "confirm my booking instantly",
                    "text": "As a patient, I want to book a consultation slot and pay the fee online, so that I can confirm my booking instantly.",
                    "acceptance_criteria": [
                        "Booking limits are verified (max 2 bookings per patient per day).",
                        "Integration with Stripe payment gateway processes the fee.",
                        "On successful payment, patient receives confirmation email with appointment details."
                    ],
                    "priority": "high",
                    "story_points": 5
                },
                {
                    "id": "US-003",
                    "role": "doctor",
                    "epic": "Patient Records",
                    "feature": "view patient history and symptoms before the call",
                    "benefit": "provide high-quality medical advice",
                    "text": "As a doctor, I want to view patient history and symptoms before the call, so that I can provide high-quality medical advice.",
                    "acceptance_criteria": [
                        "Doctor can access patient intake form details from dashboard.",
                        "Medical records must be encrypted in transit and at rest.",
                        "Doctor can write session notes directly in the record during consultation."
                    ],
                    "priority": "medium",
                    "story_points": 5
                }
            ])
        
        # Check for E-Commerce / shopping
        elif "ecommerce" in req_lower or "shop" in req_lower or "cart" in req_lower or "seller" in req_lower or "product" in req_lower:
            stories.extend([
                {
                    "id": "US-001",
                    "role": "buyer",
                    "epic": "Catalog Navigation",
                    "feature": "browse products by category and subcategory",
                    "benefit": "find items I want to buy quickly",
                    "text": "As a buyer, I want to browse products by category and subcategory, so that I can find items I want to buy quickly.",
                    "acceptance_criteria": [
                        "Categories dropdown menu is accessible on all pages.",
                        "Products load dynamically without full page reload when switching categories.",
                        "Empty categories display a helpful search suggestion page."
                    ],
                    "priority": "high",
                    "story_points": 3
                },
                {
                    "id": "US-002",
                    "role": "seller",
                    "epic": "Product Management",
                    "feature": "list a new product with images and AI-generated description",
                    "benefit": "save time and attract buyers",
                    "text": "As a seller, I want to list a new product with images and AI-generated description, so that I can save time and attract buyers.",
                    "acceptance_criteria": [
                        "Sellers can upload multiple product images via drag-and-drop.",
                        "The system generates a suggested description using a local LLM prompt based on the title.",
                        "Product listings are verified for offensive content before going live."
                    ],
                    "priority": "medium",
                    "story_points": 5
                },
                {
                    "id": "US-003",
                    "role": "buyer",
                    "epic": "Cart & Checkout",
                    "feature": "add items to shopping cart and complete payment",
                    "benefit": "receive products at my address",
                    "text": "As a buyer, I want to add items to my shopping cart and complete payment, so that I can receive products at my address.",
                    "acceptance_criteria": [
                        "Cart displays subtotal, shipping cost, tax, and grand total clearly.",
                        "Inventory level is checked before finalizing payment.",
                        "Payment is securely processed via Stripe with support for standard credit cards."
                    ],
                    "priority": "high",
                    "story_points": 8
                }
            ])
            
        # Check for fintech
        elif "fintech" in req_lower or "bank" in req_lower or "payment" in req_lower or "transaction" in req_lower:
            stories.extend([
                {
                    "id": "US-001",
                    "role": "user",
                    "epic": "Payments",
                    "feature": "send money instantly to contacts using their phone number",
                    "benefit": "make payments quickly and securely",
                    "text": "As a user, I want to send money instantly to contacts using their phone number, so that I can make payments quickly and securely.",
                    "acceptance_criteria": [
                        "Recipient must be verified before payment is initiated.",
                        "Funds transfer completes in under 2 seconds.",
                        "User must authorize transaction with a biometric or PIN verification."
                    ],
                    "priority": "high",
                    "story_points": 5
                },
                {
                    "id": "US-002",
                    "role": "user",
                    "epic": "Transactions",
                    "feature": "view detailed transaction logs and filter by date",
                    "benefit": "track my spending and bank history",
                    "text": "As a user, I want to view detailed transaction logs and filter by date, so that I can track my spending and bank history.",
                    "acceptance_criteria": [
                        "Logs display date, time, vendor name, status, and transaction amount.",
                        "Transactions are paginated (20 per page) with lazy loading.",
                        "Users can download monthly PDF statement of transactions."
                    ],
                    "priority": "medium",
                    "story_points": 3
                }
            ])

        # If no specific stories are added, provide some generic ones customized to the requirement text
        if not stories:
            topic = "the system features"
            if isinstance(project_context, dict) and project_context.get("project_title"):
                topic = project_context.get("project_title")
            elif not isinstance(project_context, dict) and len(str(project_context)) < 100:
                topic = str(project_context).strip().rstrip('.')
                
            stories.extend([
                {
                    "id": "US-001",
                    "role": "user",
                    "epic": "Core Operations",
                    "feature": f"interact with the main functions of {topic}",
                    "benefit": "achieve my goals and solve my tasks effectively",
                    "text": f"As a user, I want to interact with the main functions of {topic}, so that I can achieve my goals and solve my tasks effectively.",
                    "acceptance_criteria": [
                        "Interface must be fully responsive on mobile and desktop screens.",
                        "All user input fields are validated on submission.",
                        "Action buttons provide visual feedback (loading spinners) when clicked."
                    ],
                    "priority": "high",
                    "story_points": 3
                },
                {
                    "id": "US-002",
                    "role": "administrator",
                    "epic": "System Management",
                    "feature": f"monitor and manage {topic} configurations and users",
                    "benefit": "ensure system security and operational continuity",
                    "text": f"As an administrator, I want to monitor and manage {topic} configurations and users, so that I can ensure system security and operational continuity.",
                    "acceptance_criteria": [
                        "Admin dashboard displays real-time system logs and CPU/memory usage.",
                        "Administrator can toggle user accounts between Active and Suspended states.",
                        "System notifications are sent for high-severity exceptions."
                    ],
                    "priority": "medium",
                    "story_points": 5
                }
            ])
            
        return {"user_stories": stories}
