import subprocess, os, sys
os.chdir("/Users/neominnthu/Desktop/Project/agency")
env = os.environ.copy()
env["PYTHONPATH"] = "apps/api"

r = subprocess.run(
    [sys.executable, "-m", "pytest",
     "apps/api/tests/integration/test_auth_integration.py::TestAuthIntegration::test_signup_weak_password",
     "apps/api/tests/integration/test_auth_integration.py::TestAuthIntegration::test_signup_duplicate_email",
     "apps/api/tests/integration/test_auth_integration.py::TestAuthIntegration::test_signin_wrong_password",
     "-v", "--tb=short"],
    capture_output=True, text=True, env=env, timeout=60
)
with open("/tmp/auth_test.txt", "w") as f:
    f.write(f"Exit: {r.returncode}\n")
    f.write(r.stdout)
    f.write("\n---STDERR---\n")
    f.write(r.stderr[-2000:])
print(f"Exit: {r.returncode}")