#!/bin/bash
cd /Users/neominnthu/Desktop/Project/agency
PYTHONPATH=apps/api apps/api/.venv/bin/python -m pytest apps/api/tests/unit/test_adplatform_adapters.py::TestGoogleAdsAdapter::test_real_mode_parses_response -v --tb=long 2>&1
