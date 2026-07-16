#!/bin/bash
cd /Users/neominnthu/Desktop/Project/agency/astra-os/apps/api
python -m pytest tests/unit -v --tb=short 2>&1 | head -100