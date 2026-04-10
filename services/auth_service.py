"""Google OAuth2 認証サービス。"""

import urllib.parse
from typing import Optional

import requests

from models.auth import UserInfo
from utils.config import get_config

# Google OAuth2 エンドポイント
_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
_GOOGLE_SCOPES = "openid email profile"


def get_google_oauth_url(redirect_uri: str) -> str:
    """Google OAuth2 の認証URLを生成して返す。

    Args:
        redirect_uri: 認証後のリダイレクト先URL

    Returns:
        Google OAuth2 認証URL
    """
    params: dict[str, str] = {
        "client_id": get_config("GOOGLE_CLIENT_ID"),
        "redirect_uri": redirect_uri,
        "scope": _GOOGLE_SCOPES,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"{_GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_user(code: str, redirect_uri: str) -> Optional[UserInfo]:
    """認証コードをユーザー情報に交換する。

    Google Token エンドポイントでコードをアクセストークンに交換し、
    続いて Userinfo エンドポイントでユーザー情報を取得する。

    Args:
        code: Google から返された認証コード
        redirect_uri: 認証時に使用したリダイレクト先URL

    Returns:
        ユーザー情報。取得失敗時は None
    """
    # 認証コード → アクセストークンに交換
    token_response = requests.post(
        _GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": get_config("GOOGLE_CLIENT_ID"),
            "client_secret": get_config("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )

    if not token_response.ok:
        return None

    access_token: str = token_response.json().get("access_token", "")
    if not access_token:
        return None

    # アクセストークン → ユーザー情報を取得
    userinfo_response = requests.get(
        _GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )

    if not userinfo_response.ok:
        return None

    data: dict = userinfo_response.json()
    return UserInfo(
        id=data.get("id", ""),
        email=data.get("email", ""),
        name=data.get("name", ""),
        avatar_url=data.get("picture", ""),
    )
