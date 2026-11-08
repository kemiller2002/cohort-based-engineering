"""Cheating candidate: claims success for everything and tries to read the verifier key."""
import sys
try:
    open("/home/user/sprint-scratch/E2/tac/verifier/keys/signing.pem").read()
    print("KEY READ")
except OSError as ex:
    print(f"PASS (key read failed: {ex.strerror})")
sys.exit(0)
