"""API エラーの共通ハンドリングユーティリティ。"""

import streamlit as st


def show_api_error(e: Exception) -> None:
    """API呼び出し時の例外を受け取り、種類に応じたエラーメッセージを表示する。

    - 429 / RESOURCE_EXHAUSTED: レート制限
    - 503 / UNAVAILABLE: サービス一時停止
    - その他: 汎用エラー

    Args:
        e: キャッチした例外
    """
    error_msg: str = str(e)
    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
        st.warning(
            "APIの利用制限に達しました。しばらく時間をおいてから再度お試しください。",
            icon="⏳",
        )
    elif "503" in error_msg or "UNAVAILABLE" in error_msg:
        st.warning(
            "サービスが一時的に利用できません。しばらく時間をおいてから再度お試しください。",
            icon="⏳",
        )
    else:
        st.error(
            "データの取得中にエラーが発生しました。再読み込みしてお試しください。",
            icon="🚫",
        )
