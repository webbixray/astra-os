import subprocess, os
os.chdir("/Users/neominnthu/Desktop/Project/agency")
env = os.environ.copy()
env["PYTHONPATH"] = "apps/api"
r = subprocess.run(
    ["/Users/neominnthu/Library/Application Support/Zed/node/node-v24.11.0-darwin-x64/bin/python", "-m", "pytest",
     "apps/api/tests/integration/test_auth_integration.py::TestAuthIntegration::test_full_auth_flow",
     "-v", "--tb=long"],
    capture_output=True, text=True, env=env, timeout=60
)
with open("/tmp/auth_test_result.txt", "w") as f:
    f.write(f"Exit: {r.returncode}\n")
    f.write(r.stdout)
    f.write("\n---STDERR---\n")
    f.write(r.stderr)
print(f"Exit: {r.returncode}")