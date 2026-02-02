#!/usr/bin/env python3
"""
Gemini Deep Research API Integration.

This script submits research topics to Google's Deep Research agent
and polls for completion, displaying the final research report.

Note: Deep Research is only available through Google AI (not Vertex AI).
You need a GEMINI_API_KEY from https://aistudio.google.com/app/apikey
"""

import argparse
import os
import sys
import time

from dotenv import load_dotenv
from google import genai


def create_client() -> genai.Client:
    """Create and return a Google AI client."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        print("Get your API key from: https://aistudio.google.com/app/apikey")
        print("Then add it to your .env file: GEMINI_API_KEY=your-key-here")
        sys.exit(1)

    return genai.Client(api_key=api_key)


def run_research(client: genai.Client, topic: str) -> str:
    """
    Submit a research topic and poll until completion.

    Args:
        client: The Google AI client
        topic: The research topic/question

    Returns:
        The final research report text
    """
    print(f"Starting deep research on: {topic}")
    print("This may take several minutes...")
    print()

    # Start research in background
    interaction = client.interactions.create(
        input=topic,
        agent="deep-research-pro-preview-12-2025",
        background=True,
    )

    print(f"Research ID: {interaction.id}")
    print("Polling for completion", end="", flush=True)

    # Poll for completion
    poll_count = 0
    while True:
        interaction = client.interactions.get(interaction.id)

        if interaction.status == "completed":
            print(" Done!")
            print()
            return interaction.outputs[-1].text

        if interaction.status == "failed":
            print(" Failed!")
            print()
            error_msg = getattr(interaction, 'error', 'Unknown error')
            raise RuntimeError(f"Research failed: {error_msg}")

        # Show progress
        poll_count += 1
        if poll_count % 6 == 0:  # Every minute
            print(f" ({poll_count * 10}s)", end="", flush=True)
        else:
            print(".", end="", flush=True)

        time.sleep(10)  # Check every 10 seconds


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run deep research using Gemini Deep Research API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deep_research.py "What are the latest advances in quantum computing?"
  python deep_research.py "Compare React, Vue, and Angular for enterprise applications"

Setup:
  1. Get an API key from https://aistudio.google.com/app/apikey
  2. Add to .env file: GEMINI_API_KEY=your-key-here
        """,
    )
    parser.add_argument(
        "topic",
        help="The research topic or question to investigate",
    )
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    try:
        client = create_client()
        report = run_research(client, args.topic)

        print("=" * 80)
        print("RESEARCH REPORT")
        print("=" * 80)
        print()
        print(report)
        print()
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\nResearch cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
