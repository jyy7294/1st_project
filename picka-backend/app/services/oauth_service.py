from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException

from app.core.config import settings


OAUTH_TIMEOUT = 10.0


def oauth_config(provider: str) -> dict[str, str]:
    if provider == "KAKAO":
        values = {
            "client_id": settings.kakao_rest_api_key,
            "client_secret": settings.kakao_client_secret,
            "redirect_uri": settings.kakao_redirect_uri,
            "authorize_url": "https://kauth.kakao.com/oauth/authorize",
            "token_url": "https://kauth.kakao.com/oauth/token",
            "profile_url": "https://kapi.kakao.com/v2/user/me",
        }
    else:
        values = {
            "client_id": settings.naver_client_id,
            "client_secret": settings.naver_client_secret,
            "redirect_uri": settings.naver_redirect_uri,
            "authorize_url": "https://nid.naver.com/oauth2.0/authorize",
            "token_url": "https://nid.naver.com/oauth2.0/token",
            "profile_url": "https://openapi.naver.com/v1/nid/me",
        }
    if not all(
        values.get(key)
        for key in ("client_id", "client_secret", "redirect_uri")
    ):
        raise HTTPException(
            status_code=503,
            detail=f"{provider} 로그인 설정이 완료되지 않았습니다.",
        )
    return values  # type: ignore[return-value]


def authorization_url(provider: str, state: str) -> str:
    config = oauth_config(provider)
    parameters = {
        "client_id": config["client_id"],
        "redirect_uri": config["redirect_uri"],
        "response_type": "code",
        "state": state,
    }
    return f"{config['authorize_url']}?{urlencode(parameters)}"


async def fetch_oauth_profile(
    provider: str,
    code: str,
    state: str,
) -> dict[str, Any]:
    config = oauth_config(provider)
    token_data = {
        "grant_type": "authorization_code",
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "redirect_uri": config["redirect_uri"],
        "code": code,
    }
    if provider == "NAVER":
        token_data["state"] = state

    try:
        async with httpx.AsyncClient(timeout=OAUTH_TIMEOUT) as client:
            token_response = await client.post(
                config["token_url"],
                data=token_data,
            )
            if token_response.status_code >= 500:
                raise HTTPException(
                    status_code=502,
                    detail="외부 로그인 서비스와 통신하지 못했습니다.",
                )
            if token_response.status_code >= 400:
                raise HTTPException(
                    status_code=400,
                    detail="소셜 로그인 인증에 실패했습니다.",
                )
            access_token = token_response.json().get("access_token")
            if not access_token:
                raise HTTPException(
                    status_code=400,
                    detail="소셜 로그인 인증에 실패했습니다.",
                )

            profile_response = await client.get(
                config["profile_url"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if profile_response.status_code >= 500:
                raise HTTPException(
                    status_code=502,
                    detail="외부 로그인 서비스와 통신하지 못했습니다.",
                )
            if profile_response.status_code >= 400:
                raise HTTPException(
                    status_code=400,
                    detail="소셜 로그인 인증에 실패했습니다.",
                )
            return parse_oauth_profile(provider, profile_response.json())
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="외부 로그인 서비스와 통신하지 못했습니다.",
        ) from error


def parse_oauth_profile(
    provider: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if provider == "KAKAO":
        account = payload.get("kakao_account") or {}
        profile = account.get("profile") or {}
        provider_user_id = payload.get("id")
        result = {
            "provider_user_id": str(provider_user_id),
            "email": account.get("email"),
            "name": profile.get("nickname"),
            "profile_image_url": profile.get("profile_image_url"),
        }
    else:
        profile = payload.get("response") or {}
        provider_user_id = profile.get("id")
        result = {
            "provider_user_id": str(provider_user_id),
            "email": profile.get("email"),
            "name": profile.get("nickname") or profile.get("name"),
            "profile_image_url": profile.get("profile_image"),
        }
    if provider_user_id in (None, ""):
        raise HTTPException(
            status_code=400,
            detail="소셜 로그인 인증에 실패했습니다.",
        )
    return result
