import pytest
import sys

sys.exit(pytest.main(['-v', '--tb=long', 'apps/api/tests/unit/test_adplatform_adapters.py::TestGoogleAdsAdapter::test_real_mode_parses_response']))