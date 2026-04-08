"""予算設定画面。営業担当×月のグリッドで予算金額・目標利益率を入力・保存する。"""

from datetime import date

import pandas as pd
import streamlit as st

from controllers.budget_ctrl import BudgetCtrl

ctrl: BudgetCtrl = BudgetCtrl()

st.title("予算設定")

# 営業担当リストを取得
sales_reps: list[str] = ctrl.get_sales_reps()

# 年度リストを生成（現在年度 ± 2年）
current_year: int = date.today().year
current_month: int = date.today().month
current_fiscal_year: int = current_year if current_month >= 4 else current_year - 1
fiscal_years: list[int] = list(range(current_fiscal_year - 2, current_fiscal_year + 3))
fiscal_year_labels: list[str] = [f"{fy}年度" for fy in fiscal_years]

# 年度セレクトボックス（デフォルトは今年度）
default_index: int = fiscal_years.index(current_fiscal_year)
selected_label: str = st.selectbox("年度", fiscal_year_labels, index=default_index)
selected_fy: int = fiscal_years[fiscal_year_labels.index(selected_label)]

# 対象月リスト・グリッドデータを取得
months: list[str] = ctrl.fiscal_year_months(selected_fy)
df_amount: pd.DataFrame
df_margin: pd.DataFrame
df_amount, df_margin = ctrl.get_budget_grid(sales_reps, months)

# 売上予算グリッド
st.subheader(f"{selected_label}　売上（円）")
edited_amount: pd.DataFrame = st.data_editor(
    df_amount,
    use_container_width=True,
    key="amount",
    column_config={
        m: st.column_config.NumberColumn(format="%,d", min_value=0, step=1)
        for m in months
    },
)

# 目標利益率グリッド
st.subheader(f"{selected_label}　利益率（%）")
edited_margin: pd.DataFrame = st.data_editor(
    df_margin,
    use_container_width=True,
    key="margin",
    column_config={
        m: st.column_config.NumberColumn(format="%.1f%%", min_value=0.0, max_value=100.0, step=0.1)
        for m in months
    },
)

# 保存ボタン
if st.button("保存", type="primary"):
    ctrl.save_all(sales_reps, months, edited_amount, edited_margin)
    st.success("保存しました！")
