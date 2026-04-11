"""ログインページの描画。"""

import streamlit as st

from controllers.auth_ctrl import build_login_url


def render_login_page() -> None:
    """ログインページを描画する。"""
    _, col, _ = st.columns([1, 2, 1])

    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("業務効率化 AI ポートフォリオ")
        st.caption("ご利用にはGoogleアカウントでのログインが必要です。")
        st.markdown("<br>", unsafe_allow_html=True)

        login_url = build_login_url()
        st.link_button("🔐  Googleでログイン", url=login_url, type="primary")
