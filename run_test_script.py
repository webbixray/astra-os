#!/usr/bin/env python3
import subprocess
import sys
import os

# Change to project directory
os.chdir("/Users/neominnthu/Desktop/Project/agency/astra-os")

# Try to run pytest via python
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/unit", "-v", "--tb=short", "-x"],
    cwd="/Users/neominnthu/Desktop/Project/agency/astra-os/apps/api",
    capture_output=True,
    text=True,
    timeout=180
)

# Write output to file
with open("/Users/neominnthu/Desktop/Project/agency/astra-os/test_output.txt", "w") as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\n\nSTDERR:\n")
    f.write(result.stderr)
    f.write(f"\n\nReturn code: {result.returncode}")

print(f"Return code: {result.returncode}")
print("Output written to test_output.txt")