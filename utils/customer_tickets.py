import random
from models.state import CustomerTicket

TICKETS = {
    "basic": [
        CustomerTicket(
            id="T001",
            category="greeting",
            description="Hi, I just signed up and need help getting started.",
            priority="low"
        )
    ],
    "medium": [
        CustomerTicket(
            id="T002", 
            category="password_reset",
            description="I forgot my password and the reset link isn&#39;t working.",
            priority="medium"
        )
    ],
    "advanced": [
        CustomerTicket(
            id="T003",
            category="billing_dispute",
            description="My account was charged twice and support chat is down. Need immediate refund.",
            priority="high"
        )
    ]
}

CUSTOMER_RESPONSES = {
    "happy": ["Perfect! That&#39;s exactly what I needed.", "Thank you so much!"],
    "neutral": ["Okay, that makes sense.", "I understand."],
    "unhappy": ["Still not working.", "That didn&#39;t help."]
}

