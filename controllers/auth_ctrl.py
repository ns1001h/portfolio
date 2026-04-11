"""認証のビジネスロジック。セッション管理とOAuthフローの制御を担当する。"""

from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

from models.auth import UserInfo
from services.auth_service import exchange_code_for_user, get_google_oauth_url
from utils.config import get_config

# session_state のキー定数
_SESSION_USER = "auth_user"
_SESSION_CODE_USED = "auth_code_used"


def get_redirect_uri() -> str:
    """リダイレクトURIを返す。

    Returns:
        環境変数 GOOGLE_REDIRECT_URI の値
    """
    return get_config("GOOGLE_REDIRECT_URI")


def get_current_user() -> Optional[UserInfo]:
    """現在ログイン中のユーザーを返す。

    Returns:
        ログイン中の UserInfo。未ログイン時は None
    """
    return st.session_state.get(_SESSION_USER)


def handle_oauth_callback() -> None:
    """URLの ?code= パラメータを検出してOAuthコールバックを処理する。

    認証コードをユーザー情報に交換し、session_state に保存する。
    処理済みのコードは再利用しない。
    """
    code: str = st.query_params.get("code", "")
    if not code:
        return

    # 同一コードの二重処理を防止
    if st.session_state.get(_SESSION_CODE_USED) == code:
        return

    st.session_state[_SESSION_CODE_USED] = code

    with st.spinner("ログイン中..."):
        user = exchange_code_for_user(code, get_redirect_uri())

    if user:
        st.session_state[_SESSION_USER] = user
        # URLからcodeを除去してリロード
        st.query_params.clear()
        st.rerun()
    else:
        st.error("ログインに失敗しました。もう一度お試しください。")
        st.session_state.pop(_SESSION_CODE_USED, None)


def build_login_url() -> str:
    """Google OAuth2 のログインURLを生成して返す。

    Returns:
        Google OAuth2 認証URL
    """
    return get_google_oauth_url(get_redirect_uri())


def logout() -> None:
    """ログアウトしてセッションをクリアする。"""
    st.session_state.pop(_SESSION_USER, None)
    st.session_state.pop(_SESSION_CODE_USED, None)
    st.query_params.clear()
    st.rerun()


def render_login_page() -> None:
    """ログインページを描画する。"""
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("業務効率化 AI ポートフォリオ")
        st.caption("ご利用にはGoogleアカウントでのログインが必要です。")
        st.markdown("<br>", unsafe_allow_html=True)

        login_url = build_login_url()
        components.html(
            f"""
            <style>
                .google-btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 12px;
                    background-color: #ffffff;
                    color: #3c4043;
                    border: 1px solid #dadce0;
                    border-radius: 4px;
                    padding: 10px 24px 10px 16px;
                    font-size: 15px;
                    font-weight: 500;
                    font-family: 'Roboto', sans-serif;
                    cursor: pointer;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                    transition: box-shadow 0.2s;
                    text-decoration: none;
                }}
                .google-btn:hover {{
                    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                    background-color: #f8f9fa;
                }}
            </style>
            <a class="google-btn" href="{login_url}" target="_blank">
                <svg width="20" height="20" viewBox="0 0 48 48">
                    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
                    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
                    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
                    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.18 1.48-4.97 2.31-8.16 2.31-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
                </svg>
                Googleでログイン
            </a>
            """,
            height=60,
        )



def render_sidebar_user() -> None:
    """サイドバーにログイン中のユーザー情報とログアウトボタンを描画する。"""
    user = get_current_user()
    if not user:
        return

    with st.sidebar:
        st.divider()
        if user.avatar_url:
            st.image(user.avatar_url, width=40)
        st.caption(f"**{user.name}**")
        st.caption(user.email)
        if st.button("ログアウト", use_container_width=True):
            logout()
