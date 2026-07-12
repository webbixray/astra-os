import subprocess
import sys

result = subprocess.run([
    '/Users/neominnthu/Desktop/Project/agency/apps/api/.venv/bin/python',
    '-m', 'pytest',
    'apps/api/tests/unit/test_adplatform_adapters.py::TestGoogleAdsAdapter::test_real_mode_parses_response',
    '-v', '--tb=long'
], cwd='/Users/neominnthu/Desktop/Project/agency', env={**__import__('os').environ, 'PYTHONPATH': 'apps/api'}, capture_output=True, text=True, timeout=120)

print("STDOUT:")
print(result.stdout)
print("STDERR:")
print(result.stderr)
print("Return code:", result.returncode)