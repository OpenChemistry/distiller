import json
from urllib.parse import parse_qs

import httpx
import pytest
from authlib.integrations.httpx_client import AsyncOAuth2Client
from joserfc import jwt
from joserfc.jwk import RSAKey

import job_worker


@pytest.mark.asyncio
async def test_oauth_token_request_signs_assertion(mocker):
    """Exercise real JWT signing with a local token endpoint substitute."""
    key = RSAKey.generate_key()
    mocker.patch.object(
        job_worker.settings, "SFAPI_PRIVATE_KEY", json.dumps(key.as_dict(private=True))
    )
    mocker.patch.object(job_worker.settings, "SFAPI_CLIENT_ID", "distiller-test")
    mocker.patch.object(job_worker.settings, "SFAPI_GRANT_TYPE", "client_credentials")
    mocker.patch.object(job_worker, "_client", None)
    assertions = []

    def token_endpoint(request):
        body = parse_qs(request.content.decode())
        assertion = jwt.decode(body["client_assertion"][0], key, algorithms=["RS256"])
        assert assertion.claims["iss"] == "distiller-test"
        assert assertion.claims["sub"] == "distiller-test"
        assert assertion.claims["aud"] == job_worker.SFAPI_TOKEN_URL
        assertions.append(assertion)
        return httpx.Response(
            200,
            json={
                "access_token": "test-token",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        )

    def client_factory(**kwargs):
        return AsyncOAuth2Client(
            **kwargs, transport=httpx.MockTransport(token_endpoint)
        )

    mocker.patch.object(job_worker, "AsyncOAuth2Client", side_effect=client_factory)
    client = await job_worker.get_oauth2_client()
    try:
        assert client.token["access_token"] == "test-token"
        assert await job_worker.get_oauth2_client() is client
        assert len(assertions) == 1
    finally:
        await client.aclose()
