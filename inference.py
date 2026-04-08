#!/usr/bin/env python3
"""Baseline inference script for Smart Support Env."""

import json
import os
from typing import Dict, List

import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000")
API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")


def emit(tag: str, payload: Dict) -> None:
    print(f"[{tag}] {json.dumps(payload, separators=(',', ':'), sort_keys=False)}")


def build_prompt(observation: Dict) -> str:
    ticket = observation["current_ticket"]
    history_lines = [
        f"{turn['speaker'].title()}: {turn['message']}"
        for turn in observation["conversation_history"]
    ]
    history = "\n".join(history_lines)
    return f"""
You are a high-quality SaaS customer support agent.

Task: {observation['task_title']} ({observation['task_difficulty']})
Instructions: {observation['instructions']}
Ticket category: {ticket['category']}
Priority: {ticket['priority']}
Account tier: {ticket['account_tier']}
Customer sentiment: {ticket['sentiment']}
Customer description: {ticket['description']}
Latest customer message: {observation['latest_customer_message']}

Conversation so far:
{history}

Return only valid JSON with this shape:
{{
  "action_type": "greet|empathize|ask_clarifying_question|troubleshoot|resolve|escalate|close_ticket|update_status",
  "content": "one concise but helpful reply",
  "confidence": 0.0,
  "resolution_code": null
}}
""".strip()


def heuristic_action(task_name: str, step_count: int) -> Dict:
    plans: Dict[str, List[Dict]] = {
        "basic_greeting": [
            {
                "action_type": "greet",
                "content": "Welcome to support, and thanks for reaching out. I can help you import your first file.",
                "confidence": 0.93,
                "resolution_code": None,
            },
            {
                "action_type": "resolve",
                "content": "From the dashboard, open the Data section and choose Import to upload your CSV.",
                "confidence": 0.95,
                "resolution_code": None,
            },
            {
                "action_type": "close_ticket",
                "content": "If the import template helps, you can use it now, and support is here if you need anything else.",
                "confidence": 0.9,
                "resolution_code": None,
            },
        ],
        "medium_resolution": [
            {
                "action_type": "empathize",
                "content": "I understand the time pressure before your demo, and I'll help you get access back quickly.",
                "confidence": 0.9,
                "resolution_code": None,
            },
            {
                "action_type": "ask_clarifying_question",
                "content": "Please request the latest reset email and open only the newest email link.",
                "confidence": 0.88,
                "resolution_code": None,
            },
            {
                "action_type": "resolve",
                "content": "Use the newest reset link in a fresh browser tab so the browser does not reuse an older expired token.",
                "confidence": 0.93,
                "resolution_code": None,
            },
            {
                "action_type": "close_ticket",
                "content": "You can bookmark the login page, and if the issue returns support can help right away.",
                "confidence": 0.85,
                "resolution_code": None,
            },
        ],
        "advanced_escalation": [
            {
                "action_type": "empathize",
                "content": "I understand the impact of this double billing issue and will treat it as a priority billing case.",
                "confidence": 0.91,
                "resolution_code": None,
            },
            {
                "action_type": "ask_clarifying_question",
                "content": "Please send the invoice IDs and the timestamp for each charge so billing can verify the duplicate transaction.",
                "confidence": 0.9,
                "resolution_code": None,
            },
            {
                "action_type": "update_status",
                "content": "Our billing operations team will review the evidence and confirm the duplicate charge status after review.",
                "confidence": 0.87,
                "resolution_code": None,
            },
            {
                "action_type": "escalate",
                "content": "I am escalating this duplicate charge case to billing operations for immediate review.",
                "confidence": 0.95,
                "resolution_code": "BILLING_DUPLICATE_CHARGE",
            },
            {
                "action_type": "close_ticket",
                "content": "Your case reference is CASE-9912, and billing will update you within 24 hours.",
                "confidence": 0.88,
                "resolution_code": None,
            },
        ],
    }
    task_plan = plans[task_name]
    return task_plan[min(step_count, len(task_plan) - 1)]


def llm_action(client: OpenAI, observation: Dict) -> Dict:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0,
        messages=[{"role": "user", "content": build_prompt(observation)}],
    )
    raw_content = response.choices[0].message.content or "{}"
    return json.loads(raw_content)


def post_json(path: str, payload: Dict) -> Dict:
    response = requests.post(f"{ENV_BASE_URL}{path}", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def run_task(task_name: str, client: OpenAI | None) -> Dict:
    reset_payload = {"task_name": task_name}
    reset_result = post_json("/reset", reset_payload)
    observation = reset_result["observation"]
    finished = False
    steps = []

    emit(
        "START",
        {
            "task_name": task_name,
            "task_title": observation.get("task_title"),
            "task_difficulty": observation.get("task_difficulty"),
            "model_name": MODEL_NAME if client is not None else "heuristic-baseline",
        },
    )

    while not finished:
        if client is None:
            action = heuristic_action(task_name, observation["step_count"])
        else:
            action = llm_action(client, observation)

        step_result = post_json("/step", {"action": action})
        observation = step_result["observation"]
        reward = step_result["reward"]
        finished = step_result["done"]
        grader_score = observation.get("grader_score", 0.0)
        steps.append(
            {
                "step": observation["step_count"],
                "action_type": action["action_type"],
                "reward": reward,
                "grader_score": grader_score,
                "status": observation["status"],
            }
        )
        emit(
            "STEP",
            {
                "task_name": task_name,
                "step": observation["step_count"],
                "action_type": action["action_type"],
                "reward": reward,
                "grader_score": grader_score,
                "status": observation["status"],
                "done": finished,
            },
        )

    result = {
        "task_name": task_name,
        "final_status": observation["status"],
        "total_steps": observation["step_count"],
        "final_grader_score": steps[-1]["grader_score"] if steps else 0.0,
        "trajectory": steps,
    }
    emit(
        "END",
        {
            "task_name": task_name,
            "final_status": result["final_status"],
            "total_steps": result["total_steps"],
            "final_grader_score": result["final_grader_score"],
        },
    )
    return result


def make_client() -> OpenAI | None:
    if API_BASE_URL and MODEL_NAME and HF_TOKEN:
        return OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    return None


def main() -> None:
    client = make_client()
    task_names = ["basic_greeting", "medium_resolution", "advanced_escalation"]
    results = [run_task(task_name, client) for task_name in task_names]

    average = sum(result["final_grader_score"] for result in results) / len(results)
    emit(
        "END",
        {
            "summary": True,
            "task_count": len(results),
            "average_score": average,
            "mode": "llm" if client is not None else "heuristic",
            "model_name": MODEL_NAME if client is not None else "heuristic-baseline",
        },
    )


if __name__ == "__main__":
    main()
