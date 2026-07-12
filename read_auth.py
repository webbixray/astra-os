import subprocess, os
os.chdir("/Users/neominnthu/Desktop/Project/agency")
r = subprocess.run(["cat", "apps/api/app/presentation/routes/auth.py"], capture_output=True, text=True, timeout=10)
with open("/tmp/auth_routes.txt", "w") as f:
    f.write(r.stdout)
    f.write(r.stderr)
print("Done")