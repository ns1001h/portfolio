"""予算設定のビジネスロジックを担うコントローラー。"""

from typing import Any

import pandas as pd

from services.sales_db_service import get_deals
from services.budget_db_service import get_budgets, save_budget


class BudgetCtrl:
    """予算設定のビジネスロジックを担うコントローラー。グリッドデータ生成・保存処理を提供する。"""

    def get_sales_reps(self) -> list[str]:
        """案件データから営業担当者リストを取得して返す。"""
        df: pd.DataFrame = get_deals()
        return sorted(df["営業担当"].unique().tolist())

    def fiscal_year_months(self, fiscal_year: int) -> list[str]:
        """指定年度の月リスト（4月〜翌年3月）を返す。

        Args:
            fiscal_year: 対象年度（例: 2025）

        Returns:
            "YYYY-MM" 形式の月リスト
        """
        months: list[str] = []
        for month in range(4, 13):
            months.append(f"{fiscal_year}-{month:02d}")
        for month in range(1, 4):
            months.append(f"{fiscal_year + 1}-{month:02d}")
        return months

    def get_budget_grid(
        self, sales_reps: list[str], months: list[str]
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """営業担当×月のグリッドデータ（売上予算・目標利益率）を生成して返す。

        Args:
            sales_reps: 営業担当者リスト
            months: 対象月リスト

        Returns:
            (売上予算DataFrame, 目標利益率DataFrame) のタプル（営業担当をインデックスに設定）
        """
        amount_data: dict = {"営業担当": sales_reps}
        margin_data: dict = {"営業担当": sales_reps}

        for month in months:
            df_budget: pd.DataFrame = get_budgets(month)
            amount_map: dict[str, int] = dict(zip(df_budget["営業担当"], df_budget["予算金額"]))
            margin_map: dict[str, float] = dict(zip(df_budget["営業担当"], df_budget["目標利益率"]))
            amount_data[month] = [amount_map.get(rep, 0) for rep in sales_reps]
            margin_data[month] = [margin_map.get(rep, 15.0) for rep in sales_reps]

        df_amount: pd.DataFrame = pd.DataFrame(amount_data).set_index("営業担当")
        df_margin: pd.DataFrame = pd.DataFrame(margin_data).set_index("営業担当")
        return df_amount, df_margin

    def save_all(
        self,
        sales_reps: list[str],
        months: list[str],
        edited_amount: pd.DataFrame,
        edited_margin: pd.DataFrame,
    ) -> None:
        """編集されたグリッドデータを全件DBに保存する。

        Args:
            sales_reps: 営業担当者リスト
            months: 対象月リスト
            edited_amount: 編集済み売上予算DataFrame
            edited_margin: 編集済み目標利益率DataFrame
        """
        for rep in sales_reps:
            for month in months:
                raw_amount: Any = edited_amount.at[rep, month]
                amount: int = int(raw_amount)
                raw_margin: Any = edited_margin.at[rep, month]
                target_margin: float = float(raw_margin)
                save_budget(month, rep, amount, target_margin)
