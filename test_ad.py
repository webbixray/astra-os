import subprocess, os, sys
os.chdir("/Users/neominnthu/Desktop/Project/agency")
env = os.environ.copy()
env["PYTHONPATH"] = "apps/api"

r = subprocess.run(
    [sys.executable, "-m", "pytest",
     "apps/api/tests/integration/test_ad_platform_adapters.py",
     "-v", "--tb=short", "-x", "-q"],
    capture_output=True, text=True, env=env, timeout=60
)
with open("/tmp/ad_test.txt", "w") as f:
    f.write(f"Exit: {r.returncode}\n")
    f.write(r.stdout)
    f.write("\n---STDERR---\n")
    f.write(r.stderr[-3000:])
print(f"Exit: {r.returncode}")