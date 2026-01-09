
import os
import sys

# Mock environment variables if they are not set, just to reach the client init code
if not os.environ.get('STYTCH_PROJECT_ID'):
    os.environ['STYTCH_PROJECT_ID'] = 'project-test-00000000-0000-0000-0000-000000000000'
if not os.environ.get('STYTCH_SECRET'):
    os.environ['STYTCH_SECRET'] = 'secret-test-00000000000000000000000000000000'

try:
    from auth import get_stytch_client
    print("Attempting to initialize Stytch client...")
    client = get_stytch_client()
    print("Stytch client initialized successfully:", client)
    print("Verification Passed: No RuntimeError.")
except RuntimeError as e:
    print(f"Verification Failed: RuntimeError caught: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    sys.exit(1)
