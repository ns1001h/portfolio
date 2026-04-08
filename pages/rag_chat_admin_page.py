"""社内RAGチャット管理ページ。ドキュメントのインデックス更新を提供する。"""

import streamlit as st
from dotenv import load_dotenv

from controllers.rag_chat_admin_ctrl import RagChatAdminCtrl
from services.gemini_service import GeminiService
from services.rag_chat_vector_db_service import RagChatVectorDbService

load_dotenv()


def init_session() -> None:
    """セッション状態を初期化する。初回アクセス時のみ実行される。"""
    if "rag_chat_admin_ctrl" not in st.session_state:
        gemini: GeminiService = GeminiService()
        vector_db: RagChatVectorDbService = RagChatVectorDbService()
        st.session_state.rag_chat_admin_ctrl = RagChatAdminCtrl(gemini, vector_db)


def rag_chat_admin_page() -> None:
    """社内RAGチャット管理ページのメイン処理。"""
    st.title("社内RAGチャット 管理")

    init_session()

    ctrl: RagChatAdminCtrl = st.session_state.rag_chat_admin_ctrl

    # ── インデックス更新 ──
    st.subheader("ドキュメント更新")
    st.caption(f"インデックス状態：{ctrl.index_status}")
    if st.button("ドキュメントを更新する", type="primary"):
        with st.spinner("ドキュメントをベクトル化中...（しばらくお待ちください）"):
            success: bool
            message: str
            success, message = ctrl.update_index()
        if success:
            st.success(message)
        else:
            st.error(message)


rag_chat_admin_page()
