#!/usr/bin/env python3
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/unit", "-v", "--tb=short"],
    cwd="/Users/neominnthu/Desktop/Project/agency/astra-os/apps/api",
    capture_output=True,
    text=True,
    timeout=120
)

print("STDOUT:")
print(result.stdout[:5000])
print("\nSTDERR:")
print(result.stderr[:5000])
print(f"\nReturn code: {result.returncode}")