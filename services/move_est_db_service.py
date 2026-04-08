"""引越し見積もりのマスタデータ・過去案件をSupabaseで管理するサービス。"""

import os

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

# デフォルトの利益率
_DEFAULT_PROFIT_RATE: float = 0.3

# デフォルトの月別季節係数（1月〜12月）
_DEFAULT_SEASON_FACTORS: list[float] = [
    1.0, 1.0, 1.8, 0.8, 0.9, 1.0, 1.0, 1.1, 1.0, 0.9, 0.9, 1.1
]

# Supabaseクライアントの初期化
_client: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)


class MoveEstDbService:
    """引越し見積もりのマスタデータ（利益率・季節係数）と過去案件をSupabaseで管理するサービス。"""

    def get_all_cases(self) -> list[dict]:
        """Supabaseから全過去案件を取得して返す。"""
        response = _client.table("move_est_cases").select(
            "id, volume_m3, distance_km, cost"
        ).execute()
        return response.data or []

    def import_cases_from_df(self, df: pd.DataFrame) -> int:
        """DataFrameの案件データをSupabaseにupsertして件数を返す。

        Args:
            df: id・volume_m3・distance_km・cost カラムを持つDataFrame

        Returns:
            upsert した件数
        """
        records: list[dict] = df.rename(columns={
            "id": "id",
            "volume_m3": "volume_m3",
            "distance_km": "distance_km",
            "cost": "cost",
        })[["id", "volume_m3", "distance_km", "cost"]].to_dict(orient="records")

        # costを整数に変換する
        for rec in records:
            rec["cost"] = int(rec["cost"])

        _client.table("move_est_cases").upsert(records).execute()
        return len(records)

    def get_profit_rate(self) -> float:
        """Supabaseから利益率を取得して返す。テーブルが空の場合はデフォルト値を返す。"""
        response = _client.table("move_est_profit_rate").select("value").eq("id", 1).execute()
        if response.data:
            return float(response.data[0]["value"])
        return _DEFAULT_PROFIT_RATE

    def set_profit_rate(self, value: float) -> None:
        """Supabaseの利益率をupsertで更新する。

        Args:
            value: 新しい利益率（0〜1の範囲）
        """
        _client.table("move_est_profit_rate").upsert({"id": 1, "value": value}).execute()

    def get_season_factors(self) -> list[float]:
        """Supabaseから月別季節係数をリストで取得して返す（インデックス0=1月〜11=12月）。
        テーブルが空の場合はデフォルト値を返す。
        """
        response = _client.table("move_est_season_factors").select(
            "month, factor"
        ).order("month").execute()
        if response.data:
            return [float(row["factor"]) for row in response.data]
        return _DEFAULT_SEASON_FACTORS

    def set_season_factor(self, month: int, factor: float) -> None:
        """Supabaseの指定した月の季節係数をupsertで更新する。

        Args:
            month: 更新対象の月（1〜12）
            factor: 新しい季節係数（0より大きい値）
        """
        _client.table("move_est_season_factors").upsert(
            {"month": month, "factor": factor}
        ).execute()
