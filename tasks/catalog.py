from typing import Dict, List

from models.state import CustomerTicket


TASKS: Dict[str, Dict] = {
    "basic_greeting": {
        "difficulty": "easy",
        "title": "New User Welcome",
        "instructions": (
            "Act like a frontline support agent. Calm the customer, acknowledge the issue, "
            "and give the correct getting-started action without inventing policy."
        ),
        "max_steps": 3,
        "ticket": CustomerTicket(
            id="T-1001",
            customer_name="Ananya Rao",
            category="onboarding",
            description="I just signed up for the analytics dashboard and cannot find where to import my first CSV.",
            priority="low",
            account_tier="starter",
            sentiment="confused",
            business_impact="low",
        ),
        "initial_customer_message": (
            "Hi, I just signed up and I'm stuck. Where do I upload my first CSV file?"
        ),
        "objectives": [
            {
                "name": "greet_and_acknowledge",
                "description": "Open politely and acknowledge the onboarding problem.",
                "accepted_action_types": ["greet", "empathize"],
                "required_keywords": ["welcome", "import"],
                "progress": 0.34,
                "customer_reply": "Thanks. I mostly just need to know the first place to click.",
                "status_on_success": "in_progress",
            },
            {
                "name": "provide_correct_navigation",
                "description": "Direct the user to the import flow from the dashboard.",
                "accepted_action_types": ["troubleshoot", "resolve"],
                "required_keywords": ["data", "import"],
                "progress": 0.33,
                "customer_reply": "I found the Data menu now. Anything I should check before uploading?",
                "status_on_success": "in_progress",
            },
            {
                "name": "close_with_reassurance",
                "description": "Close politely and confirm success.",
                "accepted_action_types": ["close_ticket", "resolve"],
                "required_keywords": ["template", "help"],
                "progress": 0.33,
                "customer_reply": "Perfect, that's enough for me. Thanks for the quick help.",
                "status_on_success": "resolved",
            },
        ],
    },
    "medium_resolution": {
        "difficulty": "medium",
        "title": "Password Reset Recovery",
        "instructions": (
            "Diagnose the access issue, verify the likely cause, and guide the customer to a safe password reset resolution."
        ),
        "max_steps": 4,
        "ticket": CustomerTicket(
            id="T-2408",
            customer_name="Marcus Lee",
            category="authentication",
            description="I keep clicking the password reset email, but it says the link expired immediately.",
            priority="medium",
            account_tier="growth",
            sentiment="frustrated",
            business_impact="medium",
        ),
        "initial_customer_message": (
            "The password reset link keeps failing and I need access before the client demo this afternoon."
        ),
        "objectives": [
            {
                "name": "acknowledge_urgency",
                "description": "Recognize urgency and reassure the customer.",
                "accepted_action_types": ["greet", "empathize"],
                "required_keywords": ["understand", "demo"],
                "progress": 0.2,
                "customer_reply": "Exactly. I need the fastest path to get back in.",
                "status_on_success": "in_progress",
            },
            {
                "name": "check_root_cause",
                "description": "Ask the customer to request a fresh reset email and use the latest link only.",
                "accepted_action_types": ["ask_clarifying_question", "troubleshoot"],
                "required_keywords": ["latest", "email"],
                "progress": 0.25,
                "customer_reply": "I may have used an older email. I can request a new one now.",
                "status_on_success": "waiting_on_customer",
            },
            {
                "name": "provide_safe_resolution",
                "description": "Advise the safe reset flow and mention opening the newest link in a fresh browser tab.",
                "accepted_action_types": ["resolve", "troubleshoot"],
                "required_keywords": ["browser", "newest"],
                "progress": 0.3,
                "customer_reply": "That worked. I can sign in again now.",
                "status_on_success": "resolved",
            },
            {
                "name": "close_with_prevention_tip",
                "description": "Close the ticket and provide one prevention tip for future reset attempts.",
                "accepted_action_types": ["close_ticket", "resolve"],
                "required_keywords": ["bookmark", "support"],
                "progress": 0.25,
                "customer_reply": "Got it. I'll bookmark the login page instead of old reset emails next time.",
                "status_on_success": "closed",
            },
        ],
    },
    "advanced_escalation": {
        "difficulty": "hard",
        "title": "Duplicate Billing Charge",
        "instructions": (
            "Handle a billing dispute safely. Do not promise a refund you cannot authorize. "
            "Collect the right evidence, explain the next step, and escalate to billing operations."
        ),
        "max_steps": 5,
        "ticket": CustomerTicket(
            id="T-9912",
            customer_name="Priya Nair",
            category="billing_dispute",
            description="My company card was charged twice for the same Pro subscription renewal, and finance is escalating internally.",
            priority="high",
            account_tier="enterprise",
            sentiment="angry",
            business_impact="high",
        ),
        "initial_customer_message": (
            "We were billed twice today for the same renewal. I need this corrected before finance closes the books."
        ),
        "objectives": [
            {
                "name": "deescalate_and_acknowledge",
                "description": "Acknowledge the billing impact and avoid defensive language.",
                "accepted_action_types": ["greet", "empathize"],
                "required_keywords": ["double", "billing"],
                "progress": 0.18,
                "customer_reply": "Thanks. I need to know what you can do right now.",
                "status_on_success": "in_progress",
            },
            {
                "name": "collect_evidence",
                "description": "Ask for the invoice IDs or last four digits and charge timestamps.",
                "accepted_action_types": ["ask_clarifying_question", "troubleshoot"],
                "required_keywords": ["invoice", "timestamp"],
                "progress": 0.22,
                "customer_reply": "I have both invoice IDs and the timestamps from finance.",
                "status_on_success": "waiting_on_customer",
            },
            {
                "name": "set_expectation",
                "description": "Explain that billing operations must verify and process the refund request.",
                "accepted_action_types": ["update_status", "resolve", "troubleshoot"],
                "required_keywords": ["billing operations", "review"],
                "progress": 0.2,
                "customer_reply": "Understood. I mainly need confirmation that the case is moving.",
                "status_on_success": "in_progress",
            },
            {
                "name": "escalate_correctly",
                "description": "Escalate to billing operations with an accurate reason code.",
                "accepted_action_types": ["escalate"],
                "required_keywords": ["duplicate charge"],
                "required_resolution_code": "BILLING_DUPLICATE_CHARGE",
                "progress": 0.25,
                "customer_reply": "Okay, if billing is on it, please send me the case number.",
                "status_on_success": "escalated",
            },
            {
                "name": "close_with_case_reference",
                "description": "Provide the case reference and timeline without promising an instant refund.",
                "accepted_action_types": ["close_ticket", "update_status"],
                "required_keywords": ["case", "24 hours"],
                "progress": 0.15,
                "customer_reply": "That timeline works. I'll watch for the follow-up from billing.",
                "status_on_success": "closed",
            },
        ],
    },
}


def get_task_names() -> List[str]:
    return list(TASKS.keys())
