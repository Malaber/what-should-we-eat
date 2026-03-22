"""
example_script.py — Template for execution-layer scripts.

Delete this file and replace with actual execution scripts.
Each script should be deterministic, well-commented, and independently runnable.

Usage:
    python execution/example_script.py --input <path>
"""

import argparse
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


def main(input_path: str) -> None:
    """Main entry point."""
    print(f"Processing: {input_path}")

    # Example: read an API key from .env
    api_key = os.getenv("EXAMPLE_API_KEY")
    if not api_key:
        raise EnvironmentError("EXAMPLE_API_KEY not set in .env")

    # --- do deterministic work here ---
    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Example execution script")
    parser.add_argument("--input", required=True, help="Path to input file")
    args = parser.parse_args()
    main(args.input)
