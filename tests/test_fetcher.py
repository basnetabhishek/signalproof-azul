import pytest
from azulbrief.fetcher import normalize_domain, ensure_public_domain

def test_domain_rejects_path():
    with pytest.raises(ValueError): normalize_domain("example.com/private/path")

def test_local_domain_is_blocked():
    with pytest.raises(ValueError): ensure_public_domain("localhost")
