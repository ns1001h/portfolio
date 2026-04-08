"""引越し見積もり用ベクトルインデックスの保存・検索サービス。"""

import json
import math
from typing import Any

from supabase import Client, create_client

from models.move_est import PastCase
from utils.config import get_config


class MoveEstVectorDbService:
    """引越し見積もり用ベクトルインデックスをSupabaseで管理するサービス。案件の保存・類似検索を担う。"""

    _client: Client
    _n_results: int      # 検索結果の最大件数
    _max_distance: float # ユークリッド距離の閾値（これより遠い案件は除外）

    def __init__(self) -> None:
        """Supabaseクライアントと検索パラメータを初期化する。"""
        self._client = create_client(
            get_config("SUPABASE_URL"),
            get_config("SUPABASE_KEY"),
        )
        self._n_results = int(get_config("MOVE_EST_SEARCH_N_RESULTS", "3"))
        self._max_distance = float(get_config("MOVE_EST_SEARCH_MAX_DISTANCE", "0.6"))

    def save(self, cases: list[PastCase], updated_at: str) -> None:
        """各案件のembeddingをSupabaseに保存する。

        Args:
            cases: PastCaseのリスト（embeddingが設定済み）
            updated_at: 更新日時文字列
        """
        for case in cases:
            self._client.table("move_est_cases").update({
                "embedding": case.embedding,
                "updated_at": updated_at,
            }).eq("id", case.id).execute()

    def _parse_embedding(self, value: Any) -> list[float]:
        """Supabaseから返ってくるembeddingを list[float] に変換する。文字列の場合はJSONパースする。"""
        if isinstance(value, str):
            return [float(v) for v in json.loads(value)]
        return [float(v) for v in value]

    def _normalized_distance(
        self,
        volume_m3: float,
        distance_km: float,
        case: PastCase,
        max_volume: float,
        max_distance: float,
    ) -> float:
        """体積・距離をそれぞれ正規化してユークリッド距離を計算する（0〜√2、値が小さいほど類似）。"""
        vol_diff: float = (volume_m3 - case.volume_m3) / max_volume if max_volume > 0 else 0.0
        dist_diff: float = (distance_km - case.distance_km) / max_distance if max_distance > 0 else 0.0
        return math.sqrt(vol_diff ** 2 + dist_diff ** 2)

    def search(self, volume_m3: float, distance_km: float) -> list[tuple[float, PastCase]]:
        """体積・距離の数値で全案件を検索し、正規化ユークリッド距離が近い上位n件を返す。

        Returns:
            (ユークリッド距離, PastCase) のリスト。距離昇順。閾値超えは除外。
        """
        response = self._client.table("move_est_cases").select(
            "id, volume_m3, distance_km, cost, embedding"
        ).not_.is_("embedding", "null").execute()

        if not response.data:
            return []

        rows: list[Any] = response.data
        cases: list[PastCase] = [
            PastCase(
                id=str(row["id"]),
                volume_m3=float(row["volume_m3"]),
                distance_km=float(row["distance_km"]),
                cost=int(row["cost"]),
                embedding=self._parse_embedding(row["embedding"]),
            )
            for row in rows
        ]

        max_volume: float = max(c.volume_m3 for c in cases)
        max_distance: float = max(c.distance_km for c in cases)

        scored: list[tuple[float, PastCase]] = [
            (self._normalized_distance(volume_m3, distance_km, c, max_volume, max_distance), c)
            for c in cases
        ]
        scored.sort(key=lambda x: x[0])
        return [(dist, c) for dist, c in scored[: self._n_results] if dist <= self._max_distance]

    @property
    def status(self) -> str:
        """現在のインデックス状態を表示用文字列で返す。"""
        response = self._client.table("move_est_cases").select(
            "id, updated_at"
        ).not_.is_("embedding", "null").execute()

        rows: list[Any] = response.data or []
        if not rows:
            return "未更新"
        updated_at: str = str(rows[0]["updated_at"])
        return f"{len(rows)}件 ／ 最終更新：{updated_at}"
