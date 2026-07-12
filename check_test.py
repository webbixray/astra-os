import subprocess, os
os.chdir("/Users/neominnthu/Desktop/Project/agency")
r = subprocess.run(
    ["cat", "apps/api/tests/integration/test_auth_integration.py"],
    capture_output=True, text=True, timeout=10
)
with open("/tmp/auth_test.txt", "w") as f:
    f.write(r.stdout)
    f.write(r.stderr)
print("Done")