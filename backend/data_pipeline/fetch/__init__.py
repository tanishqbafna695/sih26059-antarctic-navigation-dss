"""Fetch clients (Phase 4). All sources free/open (zero-cost constraint §7.4).

Clients import their SDK lazily so the pipeline runs without accounts;
credentials come from environment variables (see config.Credentials).
"""


class CredentialsMissing(Exception):
    """A free account is required but its credentials are not configured."""


class ManualDownloadRequired(Exception):
    """The source has no scriptable URL configured; download by hand and place the file."""


class FetchError(Exception):
    """A download failed (network, HTTP status, or provider-side change)."""