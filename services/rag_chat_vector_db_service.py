"""社内RAGチャット用ベクトルインデックスの保存・検索サービス。"""

import json
import math
from typing import Any

from supabase import Client, create_client

from utils.config import get_config

# チャンクデータの型エイリアス（テキスト・出典ファイル名・埋め込みベクトルを保持）
ChunkData = dict


class RagChatVectorDbService:
    """社内RAGチャット用ベクトルインデックスをSupabaseで管理するサービス。保存・検索・類似度計算を担う。"""

    _client: Client
    _n_results: int    # 検索で返す最大件数
    _min_score: float  # 検索結果に含める最低類似度スコア

    def __init__(self) -> None:
        """Supabaseクライアントと検索パラメータを初期化する。"""
        self._client = create_client(
            get_config("SUPABASE_URL"),
            get_config("SUPABASE_KEY"),
        )
        self._n_results = int(get_config("RAG_CHAT_SEARCH_N_RESULTS", "5"))
        self._min_score = float(get_config("RAG_CHAT_SEARCH_MIN_SCORE", "0.5"))

    def save(self, chunks: list[ChunkData], updated_at: str) -> None:
        """チャンクデータをSupabaseに保存する。既存データは全件削除して入れ直す。

        Args:
            chunks: チャンクデータのリスト（id・text・source・embeddingを含む）
            updated_at: 更新日時文字列
        """
        # 既存データを全件削除
        self._client.table("rag_chat_chunks").delete().neq("id", "").execute()

        # 新しいチャンクを挿入
        rows: list[dict] = [
            {
                "id": chunk["id"],
                "text": chunk["text"],
                "source": chunk["source"],
                "embedding": chunk["embedding"],
                "updated_at": updated_at,
            }
            for chunk in chunks
        ]
        if rows:
            self._client.table("rag_chat_chunks").insert(rows).execute()

    def search(self, query_embedding: list[float]) -> list[tuple[float, str, str]]:
        """クエリのベクトルで全チャンクを検索し、閾値以上のスコアを持つ上位n件を返す。

        Returns:
            (スコア, テキスト, ファイル名) のタプルリスト（スコア降順）
        """
        response = self._client.table("rag_chat_chunks").select(
            "text, source, embedding"
        ).execute()

        if not response.data:
            return []

        rows: list[Any] = response.data
        # 全チャンクとのコサイン類似度を計算してスコアリング
        scored: list[tuple[float, str, str]] = [
            (
                self._cosine_similarity(query_embedding, self._parse_embedding(row["embedding"])),
                str(row["text"]),
                str(row["source"]),
            )
            for row in rows
        ]

        # スコア降順でソートして閾値以上の上位n件を返す
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for item in scored[: self._n_results] if item[0] >= self._min_score]

    def _parse_embedding(self, value: Any) -> list[float]:
        """Supabaseから返ってくるembeddingを list[float] に変換する。文字列の場合はJSONパースする。"""
        if isinstance(value, str):
            return [float(v) for v in json.loads(value)]
        return [float(v) for v in value]

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """2つのベクトルのコサイン類似度を計算する（-1〜1、値が高いほど類似）。"""
        dot: float = sum(x * y for x, y in zip(a, b))
        norm_a: float = math.sqrt(sum(x * x for x in a))
        norm_b: float = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @property
    def status(self) -> str:
        """現在のインデックス状態を表示用文字列で返す。"""
        response = self._client.table("rag_chat_chunks").select(
            "id, updated_at"
        ).execute()

        rows: list[Any] = response.data or []
        if not rows:
            return "未更新"
        updated_at: str = str(rows[0]["updated_at"])
        return f"{len(rows)}件 ／ 最終更新：{updated_at}"
