"""
llm_summary.py

This file sends the prompt to the LLM (Google Gemini) and returns the
generated incident report as text.

It has one job only: take a text prompt and return the LLM's answer.
It does not know anything about logs or DataFrames - that keeps it simple.
"""

import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

MODEL_NAME = "gemini-3.5-flash"


def generate_incident_report(prompt):
    """Send the prompt to Gemini and return the incident report text.

    The prompt (built by prompt_builder.py) contains only a summary of the
    logs - statistics, anomaly counts, clusters and a few example messages.
    The raw log file is never sent to the LLM.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add it to your environment or a .env file."
        )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return response.text
