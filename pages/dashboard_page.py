"""経営ダッシュボードのメイン画面。"""

from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from controllers.dashboard_ctrl import DashboardCtrl
from utils.error_handler import show_api_error

ctrl: DashboardCtrl = DashboardCtrl()

st.title("経営ダッシュボード")

# 年月リストを生成してセレクトボックスを表示
try:
    months: list[str] = ctrl.get_months()
except Exception as e:
    show_api_error(e)
    st.stop()
current_month: str = date.today().strftime("%Y-%m")
default_month: str = current_month if current_month in months else months[-1]
default_index: int = months.index(default_month)
selected_month: str = st.selectbox("対象年月", months, index=default_index)

# KPI集計
try:
    kpi: dict = ctrl.get_kpi(selected_month)
except Exception as e:
    show_api_error(e)
    st.stop()

# KPIカード：売上・利益・利益率・案件数
col1, col2, col3, col4 = st.columns(4)
amount_diff: int = kpi["total_amount"] - kpi["total_budget"]
amount_diff_str: str = f"+¥{amount_diff:,}" if amount_diff >= 0 else f"-¥{abs(amount_diff):,}"
col1.metric(label="売上", value=f"¥{kpi['total_amount']:,}", delta=amount_diff_str)
col1.caption(f"予算 ¥{kpi['total_budget']:,}")

profit_diff: int = kpi["total_profit"] - kpi["total_profit_budget"]
profit_diff_str: str = f"+¥{profit_diff:,}" if profit_diff >= 0 else f"-¥{abs(profit_diff):,}"
col2.metric(label="利益", value=f"¥{kpi['total_profit']:,}", delta=profit_diff_str)
col2.caption(f"予算 ¥{kpi['total_profit_budget']:,}")

margin_diff: float = kpi["profit_rate"] - kpi["avg_target_margin"]
col3.metric(label="利益率", value=f"{kpi['profit_rate']:.1f}%", delta=f"{margin_diff:+.1f}%")
col3.caption(f"予算 {kpi['avg_target_margin']:.1f}%")

col4.metric(label="案件数", value=f"{kpi['deal_count']}件")

# 達成率ゲージ（売上・利益を横並び）
_, gauge_col1, gauge_col2, _ = st.columns([1, 1, 1, 1])


def _make_gauge(value: float, title: str) -> go.Figure:
    """達成率ゲージチャートを生成する。"""
    color: str = "#4F8EF7" if value < 100 else "#2ECC71"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": "%", "font": {"size": 28}},
        title={"text": title},
        gauge={
            "axis": {"range": [0, 150], "ticksuffix": "%"},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 100], "color": "#F0F0F0"},
                {"range": [100, 150], "color": "#E8F8F0"},
            ],
            "threshold": {
                "line": {"color": "#2ECC71", "width": 3},
                "thickness": 0.75,
                "value": 100,
            },
        },
    ))
    fig.update_layout(height=250, margin=dict(t=40, b=20, l=30, r=30))
    return fig


with gauge_col1:
    st.plotly_chart(_make_gauge(kpi["achievement_rate"], "売上達成率"), use_container_width=True)
with gauge_col2:
    st.plotly_chart(_make_gauge(kpi["profit_achievement_rate"], "利益達成率"), use_container_width=True)

st.divider()

# 集計軸タブ
group_options: dict[str, str] = {
    "サービス別": "サービス",
    "顧客別": "顧客",
    "営業担当別": "営業担当",
}
tabs = st.tabs(list(group_options.keys()))
for tab, (label, group_col) in zip(tabs, group_options.items()):
    with tab:
        if kpi["deal_count"] > 0:
            summary: pd.DataFrame = ctrl.get_chart_data(selected_month, group_col)
            if group_col == "営業担当" and "予算" in summary.columns:
                fig_bar = px.bar(
                    summary, x="営業担当", y=["予算", "金額"],
                    title=f"{selected_month} 営業担当別受注金額・予算",
                    barmode="group", text_auto=True,
                    color_discrete_map={"予算": "#DDDDDD"},
                )
            else:
                fig_bar = px.bar(summary, x=group_col, y="金額", title=f"{selected_month} {label}受注金額", text_auto=True)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("該当する案件データがありません。")

# 案件一覧テーブル
st.subheader("案件一覧")
display_df: pd.DataFrame = ctrl.get_filtered_deals(selected_month).copy()
display_df["利益"] = display_df["金額"] - display_df["原価"]
display_df["利益率"] = (display_df["利益"] / display_df["金額"] * 100).round(1).astype(str) + "%"
st.dataframe(
    display_df,
    use_container_width=True,
    column_config={
        "金額": st.column_config.NumberColumn(format="¥%,.0f"),
        "原価": st.column_config.NumberColumn(format="¥%,.0f"),
        "利益": st.column_config.NumberColumn(format="¥%,.0f"),
    },
)
