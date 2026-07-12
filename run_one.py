#!/usr/bin/env python3
import subprocess, os, sys
os.chdir("/Users/neominnthu/Desktop/Project/agency")
env = os.environ.copy()
env["PYTHONPATH"] = "apps/api"

# Run one specific test with python -m pytest
r = subprocess.run(
    [sys.executable, "-m", "pytest",
     "apps/api/tests/integration/test_auth_integration.py::TestAuthIntegration::test_signup_weak_password",
     "-v", "--tb=short", "-x"],
    capture_output=True, text=True, env=env, timeout=60
)
print("STDOUT:")
print(r.stdout)
print("\nSTDERR:")
print(r.stderr)
print(f"\nExit code: {r.returncode}")