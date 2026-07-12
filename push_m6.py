import subprocess, os
os.chdir("/Users/neominnthu/Desktop/Project/agency")
r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, timeout=30)
with open("/tmp/push_m6.txt", "w") as f:
    f.write(f"Exit: {r.returncode}\n")
    f.write(r.stdout)
    f.write(r.stderr)
print(f"Exit: {r.returncode}")