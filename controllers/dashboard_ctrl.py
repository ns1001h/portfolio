"""ダッシュボードのビジネスロジックを担うコントローラー。"""

import pandas as pd

from services.sales_db_service import get_deals
from services.budget_db_service import get_budgets


class DashboardCtrl:
    """ダッシュボードのビジネスロジックを担うコントローラー。KPI集計・グラフデータ生成を提供する。"""

    def get_months(self) -> list[str]:
        """案件データから年月リストを生成して返す。"""
        df: pd.DataFrame = get_deals()
        df["年月"] = pd.to_datetime(df["日付"]).dt.to_period("M").astype(str)
        return sorted(df["年月"].unique().tolist())

    def get_kpi(self, selected_month: str) -> dict:
        """指定年月のKPI（売上・利益・利益率・案件数・予算・達成率）を集計して返す。

        Args:
            selected_month: 対象年月（例: "2025-04"）

        Returns:
            KPI値を格納した辞書
        """
        df: pd.DataFrame = get_deals()
        df["年月"] = pd.to_datetime(df["日付"]).dt.to_period("M").astype(str)
        filtered: pd.DataFrame = df[df["年月"] == selected_month].drop(columns=["年月"])

        # 実績集計
        total_amount: int = int(filtered["金額"].sum())
        total_cost: int = int(filtered["原価"].sum())
        total_profit: int = total_amount - total_cost
        profit_rate: float = (total_profit / total_amount * 100) if total_amount > 0 else 0.0
        deal_count: int = len(filtered)

        # 予算集計
        df_budget: pd.DataFrame = get_budgets(selected_month)
        total_budget: int = int(df_budget["予算金額"].sum()) if not df_budget.empty else 0
        achievement_rate: float = (total_amount / total_budget * 100) if total_budget > 0 else 0.0

        # 利益予算集計
        if not df_budget.empty:
            df_budget["利益予算"] = df_budget["予算金額"] * df_budget["目標利益率"] / 100
            total_profit_budget: int = int(df_budget["利益予算"].sum())
            avg_target_margin: float = float(df_budget["目標利益率"].mean())
        else:
            total_profit_budget = 0
            avg_target_margin = 0.0

        profit_achievement_rate: float = (
            total_profit / total_profit_budget * 100 if total_profit_budget > 0 else 0.0
        )

        return {
            "total_amount": total_amount,
            "total_cost": total_cost,
            "total_profit": total_profit,
            "profit_rate": profit_rate,
            "deal_count": deal_count,
            "total_budget": total_budget,
            "achievement_rate": achievement_rate,
            "total_profit_budget": total_profit_budget,
            "avg_target_margin": avg_target_margin,
            "profit_achievement_rate": profit_achievement_rate,
        }

    def get_filtered_deals(self, selected_month: str) -> pd.DataFrame:
        """指定年月でフィルタした案件データを返す。

        Args:
            selected_month: 対象年月（例: "2025-04"）

        Returns:
            フィルタ済みの案件DataFrame
        """
        df: pd.DataFrame = get_deals()
        df["年月"] = pd.to_datetime(df["日付"]).dt.to_period("M").astype(str)
        return df[df["年月"] == selected_month].drop(columns=["年月"])

    def get_chart_data(self, selected_month: str, group_col: str) -> pd.DataFrame:
        """指定年月・集計軸でグラフ用データを集計して返す。

        Args:
            selected_month: 対象年月
            group_col: 集計軸（"サービス" / "顧客" / "営業担当"）

        Returns:
            集計済みのDataFrame
        """
        filtered: pd.DataFrame = self.get_filtered_deals(selected_month)
        summary: pd.DataFrame = (
            filtered.groupby(group_col)["金額"].sum().reset_index()
        )
        summary = summary.sort_values("金額", ascending=False)

        # 営業担当別のみ予算を結合する
        if group_col == "営業担当":
            df_budget: pd.DataFrame = get_budgets(selected_month)
            if not df_budget.empty:
                df_budget_renamed: pd.DataFrame = df_budget.rename(columns={"予算金額": "予算"})
                summary = summary.merge(df_budget_renamed, on="営業担当", how="left").fillna(0)

        return summary
