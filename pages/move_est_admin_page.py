"""引越し見積もり管理ページ。インデックス更新・CSVインポート・マスタ管理を提供する。"""

import io

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from controllers.move_est_admin_ctrl import MoveEstAdminCtrl
from services.gemini_service import GeminiService
from services.move_est_db_service import MoveEstDbService
from services.move_est_vector_db_service import MoveEstVectorDbService

load_dotenv()


def init_session() -> None:
    """セッション状態を初期化する。初回アクセス時のみ実行される。"""
    if "move_est_admin_ctrl" not in st.session_state:
        st.session_state.move_est_admin_ctrl = MoveEstAdminCtrl(
            gemini=GeminiService(),
            vector_db=MoveEstVectorDbService(),
            db=MoveEstDbService(),
        )


def move_est_admin_page() -> None:
    """引越し見積もり管理ページのメイン処理。"""
    st.title("引越し見積もり 管理")

    init_session()
    ctrl: MoveEstAdminCtrl = st.session_state.move_est_admin_ctrl

    # ── CSVインポート ──
    st.subheader("過去案件インポート")
    uploaded_file = st.file_uploader(
        "CSVファイルを選択（id, volume_m3, distance_km, cost）",
        type="csv",
    )
    if uploaded_file is not None:
        try:
            df_csv: pd.DataFrame = pd.read_csv(io.StringIO(uploaded_file.read().decode("utf-8")))
            st.dataframe(df_csv, use_container_width=True)
            if st.button("インポートする", type="primary"):
                with st.spinner("インポート中..."):
                    count: int = ctrl.import_cases_from_csv(df_csv)
                st.success(f"{count}件をインポートしました。")
        except Exception as e:
            st.error(f"CSVの読み込みエラー：{e}")

    st.divider()

    # ── ベクトルインデックス更新 ──
    st.subheader("ベクトルインデックス更新")
    st.caption(f"現在のインデックス状態：{ctrl.index_status}")
    if st.button("インデックスを更新"):
        with st.spinner("ベクトル化中..."):
            try:
                updated: int = ctrl.update_index()
                st.success(f"{updated}件のインデックスを更新しました。")
            except Exception as e:
                st.error(f"エラー：{e}")

    st.divider()

    # ── 利益率設定 ──
    st.subheader("利益率設定")
    current_profit_rate: float = ctrl.get_profit_rate()
    new_profit_rate: float = st.number_input(
        "利益率（0〜1未満）",
        min_value=0.01,
        max_value=0.99,
        value=current_profit_rate,
        step=0.01,
        format="%.2f",
    )
    if st.button("利益率を保存"):
        try:
            ctrl.update_profit_rate(new_profit_rate)
            st.success(f"利益率を {int(new_profit_rate * 100)}% に更新しました。")
        except ValueError as e:
            st.error(f"エラー：{e}")

    st.divider()

    # ── 月別季節係数設定 ──
    st.subheader("月別季節係数設定")
    season_factors: list[float] = ctrl.get_season_factors()
    month_labels: list[str] = [f"{m}月" for m in range(1, 13)]

    cols = st.columns(6)
    new_factors: list[float] = []
    for i, (label, factor) in enumerate(zip(month_labels, season_factors)):
        with cols[i % 6]:
            new_factors.append(
                st.number_input(label, min_value=0.1, max_value=5.0, value=factor, step=0.1, format="%.1f", key=f"sf_{i}")
            )

    if st.button("季節係数を保存"):
        try:
            for month_idx, factor_val in enumerate(new_factors, start=1):
                ctrl.update_season_factor(month_idx, factor_val)
            st.success("季節係数を更新しました。")
        except ValueError as e:
            st.error(f"エラー：{e}")


move_est_admin_page()
