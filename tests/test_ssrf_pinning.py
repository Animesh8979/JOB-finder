"""Tests for the SSRF / split-horizon-DNS defense in src.scraper.

The defense rejects *any* URL whose hostname resolves to a private/loopback
address across the full set of records returned by getaddrinfo. This
prevents "split-horizon-DNS" hosts that publish a public IP for some
clients and an internal IP for others (or a single host with both DNS
records).
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from src import scraper


def test_rejects_ipv4_loopback_in_url():
    with pytest.raises(ValueError):
        scraper.validate_url_for_ssrf("http://127.0.0.1/admin")


def test_rejects_private_10_network():
    with pytest.raises(ValueError):
        scraper.validate_url_for_ssrf("http://10.0.0.5/")


def test_rejects_private_192_network():
    with pytest.raises(ValueError):
        scraper.validate_url_for_ssrf("http://192.168.1.1/")


def test_rejects_non_http_scheme():
    with pytest.raises(ValueError):
        scraper.validate_url_for_ssrf("file:///etc/passwd")


def test_rejects_ftp_scheme():
    with pytest.raises(ValueError):
        scraper.validate_url_for_ssrf("ftp://example.com/")


def test_rejects_when_one_of_many_addresses_is_private():
    """A split-horizon-DNS host returns both a public and a private IP.
    The new defense must reject the URL because ANY private IP trips it.
    """
    fake_records = [
        (2, 1, 6, "", ("8.8.8.8", 0)),       # public
        (2, 1, 6, "", ("10.0.0.5", 0)),      # private — must trip rejection
    ]
    with patch("src.scraper.socket.getaddrinfo", return_value=fake_records):
        with pytest.raises(ValueError):
            scraper.validate_url_for_ssrf("http://attacker.example/")


def test_accepts_pure_public_address():
    fake_records = [
        (2, 1, 6, "", ("8.8.8.8", 0)),
        (2, 1, 6, "", ("1.1.1.1", 0)),
    ]
    with patch("src.scraper.socket.getaddrinfo", return_value=fake_records):
        ip = scraper.validate_url_for_ssrf("http://example.com/")
        assert ip in {"8.8.8.8", "1.1.1.1"}
