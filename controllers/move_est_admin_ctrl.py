"""引越し見積もり管理のビジネスロジックを担うコントローラー。"""

from datetime import datetime

import pandas as pd

from models.move_est import PastCase
from services.gemini_service import GeminiService
from services.move_est_db_service import MoveEstDbService
from services.move_est_vector_db_service import MoveEstVectorDbService


class MoveEstAdminCtrl:
    """引越し見積もり管理のビジネスロジックを担うコントローラー。インデックス更新・CSVインポート・マスタ管理を提供する。"""

    _gemini: GeminiService
    _vector_db: MoveEstVectorDbService
    _db: MoveEstDbService

    def __init__(
        self,
        gemini: GeminiService,
        vector_db: MoveEstVectorDbService,
        db: MoveEstDbService,
    ) -> None:
        """サービスを受け取って保持する。"""
        self._gemini = gemini
        self._vector_db = vector_db
        self._db = db

    @property
    def index_status(self) -> str:
        """現在のベクトルインデックス状態を表示用文字列で返す。"""
        return self._vector_db.status

    def update_index(self) -> int:
        """Supabaseの過去案件をベクトル化してベクトルDBに保存する。保存件数を返す。"""
        cases: list[PastCase] = []
        for row in self._db.get_all_cases():
            volume: float = row["volume_m3"]
            distance: float = row["distance_km"]
            embed_text: str = f"体積{volume:.1f}m³ 距離{distance:.0f}km"
            embedding: list[float] = self._gemini.embed(embed_text)
            cases.append(PastCase(
                id=row["id"],
                volume_m3=volume,
                distance_km=distance,
                cost=row["cost"],
                embedding=embedding,
            ))
        updated_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._vector_db.save(cases, updated_at)
        return len(cases)

    def import_cases_from_csv(self, df: pd.DataFrame) -> int:
        """CSVのDataFrameをSupabaseにインポートして件数を返す。

        Args:
            df: id・volume_m3・distance_km・cost カラムを持つDataFrame

        Returns:
            インポートした件数
        """
        return self._db.import_cases_from_df(df)

    def get_profit_rate(self) -> float:
        """現在の利益率をDBから取得して返す。"""
        return self._db.get_profit_rate()

    def update_profit_rate(self, value: float) -> None:
        """利益率を検証してDBに保存する（0より大きく1未満）。"""
        if not (0 < value < 1):
            raise ValueError(f"利益率は0より大きく1未満の値を入力してください（入力値：{value}）")
        self._db.set_profit_rate(value)

    def get_season_factors(self) -> list[float]:
        """月別季節係数をDBから取得して返す（インデックス0=1月〜11=12月）。"""
        return self._db.get_season_factors()

    def update_season_factor(self, month: int, factor: float) -> None:
        """指定した月の季節係数を検証してDBに保存する（0より大きい値）。"""
        if factor <= 0:
            raise ValueError(f"季節係数は0より大きい値を入力してください（入力値：{factor}）")
        self._db.set_season_factor(month, factor)
