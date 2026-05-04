import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from osint.services.crt_sh import query_crt_sh, CrtShEntry


@pytest.mark.asyncio
async def test_returns_deduplicated_subdomains():
    raw_response = [
        {"name_value": "mail.acme.com", "issuer_name": "Let's Encrypt", "not_before": "2024-01-01", "not_after": "2025-01-01"},
        {"name_value": "mail.acme.com", "issuer_name": "Let's Encrypt", "not_before": "2024-01-01", "not_after": "2025-01-01"},
        {"name_value": "vpn.acme.com", "issuer_name": "DigiCert", "not_before": "2024-01-01", "not_after": "2025-01-01"},
    ]
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value=raw_response)
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch('osint.services.crt_sh.httpx.AsyncClient', return_value=mock_client):
        results = await query_crt_sh("acme.com")

    assert len(results) == 2
    names = {r.name_value for r in results}
    assert "mail.acme.com" in names
    assert "vpn.acme.com" in names


@pytest.mark.asyncio
async def test_raises_on_invalid_domain():
    with pytest.raises(ValueError):
        await query_crt_sh("not_a_domain")


@pytest.mark.asyncio
async def test_raises_on_internal_domain():
    with pytest.raises(ValueError):
        await query_crt_sh("domain.internal")


@pytest.mark.asyncio
async def test_handles_empty_response():
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value=[])
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch('osint.services.crt_sh.httpx.AsyncClient', return_value=mock_client):
        results = await query_crt_sh("acme.com")

    assert results == []
