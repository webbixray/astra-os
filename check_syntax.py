import subprocess, os, sys
os.chdir("/Users/neominnthu/Desktop/Project/agency")
env = os.environ.copy()
env["PYTHONPATH"] = "apps/api"
venv_python = "apps/api/.venv/bin/python"
r = subprocess.run(
    [venv_python, "-m", "py_compile", "apps/api/app/presentation/routes/campaigns/campaign_routes.py"],
    capture_output=True, text=True, env=env, timeout=30
)
print("Exit:", r.returncode)
if r.returncode != 0:
    print("STDOUT:", r.stdout)
    print("STDERR:", r.stderr)
else:
    print("Syntax OK")