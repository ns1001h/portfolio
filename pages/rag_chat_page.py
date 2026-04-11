"""社内RAGチャットページ。ベクトル検索 + Gemini による RAG 回答。"""

import streamlit as st

from controllers.rag_chat_ctrl import RagChatCtrl
from services.gemini_service import GeminiService
from services.rag_chat_vector_db_service import RagChatVectorDbService
from utils.config import get_config
from utils.error_handler import show_api_error


def init_session() -> None:
    """セッション状態を初期化する。初回アクセス時のみ実行される。"""
    if "rag_chat_history" not in st.session_state:
        # 会話履歴: {"role": "user"/"assistant", "text": "...", "debug": "..."} のリスト
        st.session_state.rag_chat_history = []
    if "rag_chat_ctrl" not in st.session_state:
        gemini: GeminiService = GeminiService()
        vector_db: RagChatVectorDbService = RagChatVectorDbService()
        st.session_state.rag_chat_ctrl = RagChatCtrl(gemini, vector_db)


def is_debug_mode() -> bool:
    """DEBUG_MODE 環境変数が 1 のとき True を返す。"""
    return get_config("DEBUG_MODE", "0") == "1"


def display_history() -> None:
    """会話履歴をチャット形式で表示する。"""
    debug_mode: bool = is_debug_mode()
    for entry in st.session_state.rag_chat_history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["text"])
            # デバッグモードのときのみデバッグ情報を表示
            if debug_mode and entry.get("debug"):
                with st.expander("デバッグ情報", expanded=False):
                    st.code(entry["debug"], language=None)


def handle_input(user_text: str) -> None:
    """ユーザー入力をコントローラー経由でRAGパイプラインに通して回答を表示する。

    Args:
        user_text: ユーザーが入力した質問テキスト
    """
    debug_mode: bool = is_debug_mode()
    ctrl: RagChatCtrl = st.session_state.rag_chat_ctrl

    # ユーザーメッセージを履歴に追加して表示
    st.session_state.rag_chat_history.append({"role": "user", "text": user_text, "debug": ""})
    with st.chat_message("user"):
        st.markdown(user_text)

    # コントローラー経由でRAGパイプラインを実行して回答を表示
    with st.chat_message("assistant"):
        try:
            with st.spinner("ドキュメントを検索中..."):
                ai_text: str
                debug_info: str
                ai_text, debug_info = ctrl.get_response(user_text)
            st.markdown(ai_text)
            if debug_mode:
                with st.expander("デバッグ情報", expanded=False):
                    st.code(debug_info, language=None)
            st.session_state.rag_chat_history.append({"role": "assistant", "text": ai_text, "debug": debug_info})
        except Exception as e:
            show_api_error(e)


def rag_chat_page() -> None:
    """社内RAGチャットページのメイン処理。"""
    st.title("社内RAGチャット")

    init_session()

    # 会話をリセットするボタン
    if st.session_state.rag_chat_history:
        if st.button("会話をリセット", icon="🗑️"):
            st.session_state.rag_chat_history = []
            st.rerun()

    # 会話履歴を表示
    display_history()

    # チャット入力欄
    user_input: str | None = st.chat_input("社内規定・FAQについて質問する...")
    if user_input:
        handle_input(user_input)


rag_chat_page()
