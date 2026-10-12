"""
VoiceStudy AI - Standalone Lyzr V3 Agent Test Script
Endpoint: https://agent-prod.studio.lyzr.ai/v3/inference/chat/

Tests real Lyzr Agent Studio connectivity via the V3 REST API chat endpoint.
Safely reads credentials from environment variables / .env and never exposes secrets.
"""

import os
import sys
import json
from pathlib import Path

# 1. Load environment variables from .env file if available
try:
    from dotenv import load_dotenv, find_dotenv
    # Look for .env across project root, backend folder, and current working directory
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / ".env",
        script_dir / "backend" / ".env",
        Path.cwd() / ".env",
        Path.cwd() / "backend" / ".env",
        script_dir.parent / ".env"
    ]
    loaded = False
    for cand in candidates:
        if cand.is_file():
            load_dotenv(dotenv_path=cand, override=True)
            loaded = True
    if not loaded:
        found = find_dotenv(usecwd=True)
        if found:
            load_dotenv(dotenv_path=found, override=True)
        else:
            load_dotenv(override=True)
except ImportError:
    pass

# 2. Configuration constants & environment variable retrieval
ENDPOINT_URL = os.getenv("LYZR_CHAT_URL", "https://agent-prod.studio.lyzr.ai/v3/inference/chat/").strip()
LYZR_API_KEY = os.getenv("LYZR_API_KEY", "").strip()
LYZR_AGENT_ID = os.getenv("LYZR_AGENT_ID", "").strip()
LYZR_USER_ID = os.getenv("LYZR_USER_ID", "default_student").strip()
REQUEST_TIMEOUT_SECONDS = 60.0

TEST_MESSAGE = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TEST_MESSAGE", "Explain Python functions in simple words")


def sanitize_text(text: str, secret: str) -> str:
    """Masks the API key from any output string if present."""
    if secret and secret in text:
        return text.replace(secret, "[REDACTED_LYZR_KEY]")
    return text


def run_lyzr_test():
    print("=" * 60)
    print(" VoiceStudy AI - Lyzr Agent Studio Connectivity Test")
    print("=" * 60)
    print(f"Target Endpoint : {ENDPOINT_URL}")
    print(f"User ID         : {LYZR_USER_ID}")
    print(f"Agent ID        : {LYZR_AGENT_ID if LYZR_AGENT_ID else '[NOT SET]'}")
    print(f"API Key Status  : {'Configured (Protected - never displayed)' if LYZR_API_KEY else '[NOT SET]'}")
    print(f"Timeout         : {REQUEST_TIMEOUT_SECONDS}s")
    print("-" * 60)

    # Validate required credentials
    if not LYZR_API_KEY or "your_api_key_here" in LYZR_API_KEY:
        print("\n[ERROR] Missing or placeholder LYZR_API_KEY.")
        print("Please set your genuine Lyzr API key in the environment or .env file:")
        print("  Windows PowerShell: $env:LYZR_API_KEY=\"your-actual-api-key\"")
        print("  Linux / macOS     : export LYZR_API_KEY=\"your-actual-api-key\"")
        print("  Or add to .env    : LYZR_API_KEY=your-actual-api-key\n")
        sys.exit(1)

    if not LYZR_AGENT_ID or "your_lyzr_agent_id_here" in LYZR_AGENT_ID:
        print("\n[ERROR] Missing or placeholder LYZR_AGENT_ID.")
        print("Please set your Lyzr Agent ID in the environment or .env file:")
        print("  Windows PowerShell: $env:LYZR_AGENT_ID=\"your-agent-id\"")
        print("  Linux / macOS     : export LYZR_AGENT_ID=\"your-agent-id\"")
        print("  Or add to .env    : LYZR_AGENT_ID=your-agent-id\n")
        sys.exit(1)

    headers = {
        "x-api-key": LYZR_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "user_id": LYZR_USER_ID,
        "agent_id": LYZR_AGENT_ID,
        "session_id": f"{LYZR_USER_ID}_test_session",
        "message": TEST_MESSAGE
    }

    print(f"Sending message:\n  \"{TEST_MESSAGE.replace(chr(10), ' ')}\"\n")
    print("Awaiting Lyzr Agent response (up to 60 seconds)...")

    # Use httpx if available, fallback to urllib
    try:
        try:
            import httpx
            use_httpx = True
        except ImportError:
            use_httpx = False

        if use_httpx:
            import httpx
            with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
                response = client.post(ENDPOINT_URL, headers=headers, json=payload)
                status_code = response.status_code
                response_text = response.text
        else:
            import urllib.request
            import urllib.error
            json_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(ENDPOINT_URL, data=json_data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                    status_code = resp.getcode()
                    response_text = resp.read().decode("utf-8")
            except urllib.error.HTTPError as he:
                status_code = he.code
                response_text = he.read().decode("utf-8")
            except urllib.error.URLError as ue:
                print(f"\n[NETWORK ERROR] Could not reach Lyzr endpoint: {ue.reason}")
                sys.exit(1)

        print(f"\nHTTP Status Code: {status_code}")

        if status_code in (200, 201):
            try:
                data = json.loads(response_text)
                # Parse standard Lyzr response structures
                answer = (
                    data.get("response") or
                    data.get("message") or
                    data.get("output") or
                    (data.get("data", {}).get("response") if isinstance(data.get("data"), dict) else None)
                )
                print("\n" + "=" * 60)
                print(" LYZR AGENT RESPONSE:")
                print("=" * 60)
                if answer:
                    print(sanitize_text(str(answer).strip(), LYZR_API_KEY))
                else:
                    # Print formatted JSON if response key isn't standard
                    print(sanitize_text(json.dumps(data, indent=2), LYZR_API_KEY))
                print("=" * 60)
                print("\n[SUCCESS] Lyzr Agent test completed successfully!")
            except json.JSONDecodeError:
                print("\n[SUCCESS] Raw response (non-JSON):")
                print(sanitize_text(response_text, LYZR_API_KEY))
        elif status_code in (401, 403):
            print(f"\n[ERROR: HTTP {status_code} Authentication Failed]")
            print("Authentication failed. Please verify that your LYZR_API_KEY is active and valid.")
            clean_err = sanitize_text(response_text[:300], LYZR_API_KEY)
            print(f"Server response: {clean_err}")
            sys.exit(1)
        elif status_code == 404:
            print("\n[ERROR: 404 Not Found]")
            print(f"Agent ID '{LYZR_AGENT_ID}' or endpoint was not found. Please verify your LYZR_AGENT_ID.")
            clean_err = sanitize_text(response_text[:300], LYZR_API_KEY)
            print(f"Server response: {clean_err}")
            sys.exit(1)
        else:
            clean_err = sanitize_text(response_text[:400], LYZR_API_KEY)
            print(f"\n[API ERROR: HTTP {status_code}]")
            print(f"Details: {clean_err}")
            sys.exit(1)

    except Exception as e:
        error_name = type(e).__name__
        if "Timeout" in error_name:
            print(f"\n[TIMEOUT ERROR] Request timed out after {REQUEST_TIMEOUT_SECONDS} seconds.")
            print("The Lyzr agent took longer than 60 seconds to respond.")
        else:
            safe_err = sanitize_text(str(e), LYZR_API_KEY)
            print(f"\n[ERROR] Request failed: {safe_err}")
        sys.exit(1)


if __name__ == "__main__":
    run_lyzr_test()
