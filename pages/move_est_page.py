"""引越し見積もりページ。Gemini + ベクトル検索による見積もり算出。"""

from datetime import date

import streamlit as st

from controllers.move_est_ctrl import MoveEstCtrl
from models.move_est import MoveEstResult
from services.gemini_service import GeminiService
from services.move_est_db_service import MoveEstDbService
from services.move_est_vector_db_service import MoveEstVectorDbService
from utils.config import get_config
from utils.error_handler import show_api_error

# 家具・荷物の選択肢リスト
FURNITURE_ITEMS: list[str] = [
    "ソファ（1人掛け）", "ソファ（2人掛け）", "ソファ（3人掛け）",
    "ダイニングテーブル", "ダイニングチェア",
    "シングルベッド（フレーム＋マットレス）", "ダブルベッド（フレーム＋マットレス）",
    "タンス・衣装ケース", "本棚",
    "テレビ（32インチ以下）", "テレビ（50インチ以上）",
    "冷蔵庫（200L以下）", "冷蔵庫（400L以上）",
    "洗濯機", "電子レンジ", "食器棚", "デスク",
    "カーテン一式", "自転車", "段ボール箱（1箱）",
]

# 47都道府県リスト
PREFECTURES: list[str] = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県",
    "岐阜県", "静岡県", "愛知県", "三重県",
    "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]


def init_session() -> None:
    """セッション状態を初期化する。初回アクセス時のみ実行される。"""
    if "move_est_ctrl" not in st.session_state:
        st.session_state.move_est_ctrl = MoveEstCtrl(
            gemini=GeminiService(),
            vector_db=MoveEstVectorDbService(),
            db=MoveEstDbService(),
        )


def is_debug_mode() -> bool:
    """DEBUG_MODE 環境変数が 1 のとき True を返す。"""
    return get_config("DEBUG_MODE", "0") == "1"


def move_est_page() -> None:
    """引越し見積もりページのメイン処理。"""
    st.title("引越し見積もり")

    init_session()
    ctrl: MoveEstCtrl = st.session_state.move_est_ctrl

    # ── 入力フォーム ──
    col_date, col_from, col_to = st.columns(3)
    with col_date:
        move_date: date = st.date_input("引越し予定日", value=date.today())
    with col_from:
        from_pref: str = st.selectbox("出発地", PREFECTURES, index=12)  # 東京都
    with col_to:
        to_pref: str = st.selectbox("目的地", PREFECTURES, index=26)    # 大阪府

    st.markdown("**家具・荷物**")
    cols = st.columns(4)
    selected_furniture: list[str] = []
    for i, item in enumerate(FURNITURE_ITEMS):
        with cols[i % 4]:
            if st.checkbox(item, key=f"furniture_{i}"):
                selected_furniture.append(item)

    st.divider()

    if st.button("見積もりを算出", type="primary"):
        if not selected_furniture:
            st.warning("家具・荷物を1つ以上選択してください。")
            return

        with st.spinner("Geminiが体積・距離を推定中..."):
            try:
                result: MoveEstResult = ctrl.get_estimate(
                    move_date=str(move_date),
                    from_pref=from_pref,
                    to_pref=to_pref,
                    furniture=selected_furniture,
                )
            except Exception as e:
                show_api_error(e)
                return

        # ── 結果表示 ──
        st.subheader(f"見積金額：¥{result.estimate:,}")

        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("推定体積", f"{result.volume_m3:.1f} m³")
        res_col2.metric("推定距離", f"{result.distance_km:.0f} km")
        res_col3.metric("参考原価", f"¥{result.base_cost:,}")

        month: int = int(str(move_date).split("-")[1])
        st.caption(
            f"季節係数：{result.season_factor}（{month}月）　"
            f"利益率：{int(result.profit_rate * 100)}%"
        )

        # デバッグ情報
        if is_debug_mode() and result.debug_logs:
            with st.expander("デバッグ情報", expanded=False):
                st.code("\n\n".join(result.debug_logs), language=None)


move_est_page()
