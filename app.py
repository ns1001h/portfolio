"""経営ダッシュボードアプリのエントリーポイント。"""

import streamlit as st

# ページ設定
st.set_page_config(page_title="業務効率化 AI ポートフォリオ", layout="wide")

# 全ページ共通のトップパディング縮小
st.markdown(
    """
    <style>
        .block-container { padding-top: 1.5rem; }
        [data-testid="stSidebar"] { min-width: 170px; }
        [data-testid="stPageLink"] a,
        [data-testid="stPageLink"] a p,
        [data-testid="stPageLink"] a span {
            font-size: 1.6rem !important;
            font-weight: 600 !important;
            text-decoration: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def top_page() -> None:
    """トップページを表示する。"""
    st.title("業務効率化 AI ポートフォリオ")
    st.caption("Python × Streamlit × Google Gemini × Supabase で構築したポートフォリオアプリです。左のメニューから各機能をお試しください。")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.page_link("pages/secure_chat_page.py", label="💬 セキュアAIチャット")
        st.write(
            "機密情報漏洩対策を実装した企業向け AI チャット。"
            "正規表現フィルタとシステムプロンプトによる二重防御で、"
            "個人情報・顧客情報の外部送信を自動ブロックします。"
        )
        st.divider()

        st.page_link("pages/rag_chat_page.py", label="🤖 社内RAGチャット")
        st.write(
            "社内規定・FAQ ドキュメントを AI が検索して回答する RAG システム。"
            "問い合わせ対応の属人化を解消し、新人でも即日自己解決できる環境を実現します。"
        )
        st.divider()

    with col2:
        st.page_link("pages/move_est_page.py", label="🚚 引越し見積もり")
        st.write(
            "過去の案件データをベクトルDBに蓄積し、新規依頼との類似度検索で見積もりを自動算出。"
            "Geminiによる体積・距離の推定も組み合わせた RAG 応用デモです。"
        )
        st.divider()

        st.page_link("pages/dashboard_page.py", label="📊 経営ダッシュボード")
        st.write(
            "売上・利益・予算達成率をリアルタイムで可視化。"
            "経営層が知りたい KPI を一画面に集約し、月次レビューの準備時間を大幅に削減します。"
        )


# ナビゲーション定義（ファイル名とは別にメニュー名を指定）
pg = st.navigation({
    "メニュー": [
        st.Page(top_page, title="TOP", icon="🏠"),
        st.Page("pages/secure_chat_page.py", title="セキュアAIチャット", icon="🔒"),
        st.Page("pages/rag_chat_page.py", title="社内RAGチャット", icon="🤖"),
        st.Page("pages/move_est_page.py", title="引越し見積もり", icon="🚚"),
        st.Page("pages/dashboard_page.py", title="経営ダッシュボード", icon="📊"),
    ],
    "管理メニュー": [
        st.Page("pages/rag_chat_admin_page.py", title="社内RAGチャット 管理", icon="⚙️"),
        st.Page("pages/move_est_admin_page.py", title="引越し見積もり 管理", icon="⚙️"),
        st.Page("pages/budget_page.py", title="予算設定", icon="🎯"),
    ],
})
pg.run()
