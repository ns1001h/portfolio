"""認証のビジネスロジック。セッション管理とOAuthフローの制御を担当する。"""

from typing import Optional

import streamlit as st

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
    # 中央寄せのレイアウト
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("業務効率化 AI ポートフォリオ")
        st.caption("ご利用にはGoogleアカウントでのログインが必要です。")
        st.markdown("<br>", unsafe_allow_html=True)

        login_url = build_login_url()
        # デバッグ用：完全なURLを表示（確認後に削除）
        st.code(login_url, language=None)
        st.markdown(
            f"""
            <a href="{login_url}" target="_self" style="
                display: inline-block;
                background-color: #4285F4;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                text-decoration: none;
                font-size: 16px;
                font-weight: 600;
            ">
                🔐 &nbsp; Googleでログイン
            </a>
            """,
            unsafe_allow_html=True,
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
