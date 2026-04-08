"""セキュアAIチャットページ（機密情報漏洩対策機能付き）。"""

import streamlit as st

from controllers.secure_chat_ctrl import SecureChatCtrl
from models.pii_detection import PiiDetectionResult
from services.gemini_service import GeminiService


def init_session() -> None:
    """セッション状態を初期化する。初回アクセス時のみ実行される。"""
    if "secure_chat_history" not in st.session_state:
        # 会話履歴: {"role": "user"/"model", "text": "..."} のリスト
        st.session_state.secure_chat_history = []
    # 古いインスタンスがキャッシュされていた場合は再生成する
    if "secure_chat_ctrl" not in st.session_state or not hasattr(st.session_state.secure_chat_ctrl, "check_pii"):
        st.session_state.secure_chat_ctrl = SecureChatCtrl(GeminiService())


def display_history() -> None:
    """会話履歴をチャット形式で表示する。"""
    for entry in st.session_state.secure_chat_history:
        # Gemini APIのroleは"user"/"model"、st.chat_messageは"user"/"assistant"
        display_role: str = "assistant" if entry["role"] == "model" else "user"
        with st.chat_message(display_role):
            st.markdown(entry["text"])


def display_pii_warning(result: PiiDetectionResult) -> None:
    """機密情報が検出された場合の警告UIを表示する。

    Args:
        result: PII検出結果
    """
    types_str: str = "、".join(result.detected_types)
    st.error(
        f"**機密情報が検出されたため、送信をブロックしました**\n\n"
        f"検出された情報の種類: `{types_str}`\n\n"
        f"個人情報・顧客情報・機密情報を含むメッセージは送信できません。"
        f"情報を取り除いてから再度お試しください。",
        icon="🚫",
    )
    # マスク済みテキストをプレビュー表示
    with st.expander("マスク処理後のテキストを確認"):
        st.code(result.masked_text, language=None)


def handle_input(user_text: str) -> None:
    """ユーザー入力をコントローラー経由でGeminiに送信し、応答を会話履歴に追記する。

    機密情報が検出された場合はAPIへの送信をブロックし、警告を表示する。

    Args:
        user_text: ユーザーが入力したテキスト
    """
    ctrl: SecureChatCtrl = st.session_state.secure_chat_ctrl

    # 送信前に機密情報チェック（第1防衛線）
    pii_result: PiiDetectionResult = ctrl.check_pii(user_text)
    if pii_result.has_pii:
        # ユーザーの入力をチャットUIに表示した上でブロック警告を出す
        with st.chat_message("user"):
            st.markdown(user_text)
        display_pii_warning(pii_result)
        return

    # 機密情報なし: 履歴に追加して送信
    st.session_state.secure_chat_history.append({"role": "user", "text": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    # コントローラー経由でGeminiに問い合わせてAI応答を表示
    with st.chat_message("assistant"):
        try:
            with st.spinner("考え中..."):
                history: list[dict[str, str]] = st.session_state.secure_chat_history[:-1]
                ai_text: str = ctrl.send_message(user_text, history)
            st.markdown(ai_text)
            st.session_state.secure_chat_history.append({"role": "model", "text": ai_text})
        except Exception as e:
            error_msg: str = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                st.warning("APIの利用制限に達しました。しばらく時間をおいてから再度お試しください。", icon="⏳")
            elif "503" in error_msg or "UNAVAILABLE" in error_msg:
                st.warning("APIが一時的に混雑しています。しばらく時間をおいてから再度お試しください。", icon="⏳")
            else:
                st.error(f"エラーが発生しました: {error_msg}", icon="🚫")


def secure_chat_page() -> None:
    """セキュアAIチャットページのメイン処理。"""
    st.title("セキュアAIチャット")

    # セキュリティポリシーの案内
    with st.expander("セキュリティポリシー"):
        st.info(
            "このチャットボットは企業向けの機密情報漏洩対策を実装しています。\n\n"
            "**自動ブロック対象（第1防衛線: 送信前に検出）**\n"
            "- 電話番号、メールアドレス\n"
            "- マイナンバー、クレジットカード番号、銀行口座番号\n"
            "- 郵便番号、顧客ID、社員番号、内部IPアドレス\n\n"
            "**AIによる判断（第2防衛線: AIが文脈で判断）**\n"
            "- 氏名・顧客名などパターン外の機密情報\n"
            "- 社内識別子・契約情報を含む文章"
        )

    init_session()

    # 会話履歴をクリアするボタン
    if st.session_state.secure_chat_history:
        if st.button("会話をリセット", icon="🗑️"):
            st.session_state.secure_chat_history = []
            st.rerun()

    # 会話履歴を表示
    display_history()

    # チャット入力欄
    user_input: str | None = st.chat_input("Geminiに質問する...")
    if user_input:
        handle_input(user_input)


secure_chat_page()
