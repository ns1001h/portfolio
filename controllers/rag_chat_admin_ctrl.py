"""社内RAGチャット管理のビジネスロジックを担うコントローラー。"""

import os
from datetime import datetime

from services.gemini_service import GeminiService
from services.rag_chat_vector_db_service import ChunkData, RagChatVectorDbService
from utils.config import get_config


class RagChatAdminCtrl:
    """社内RAGチャット管理のビジネスロジックを担うコントローラー。インデックス更新を提供する。"""

    _gemini: GeminiService
    _vector_db: RagChatVectorDbService

    def __init__(self, gemini: GeminiService, vector_db: RagChatVectorDbService) -> None:
        """GeminiServiceとRagChatVectorDbServiceを受け取って保持する。"""
        self._gemini = gemini
        self._vector_db = vector_db

    @property
    def index_status(self) -> str:
        """現在のインデックス状態を表示用文字列で返す。"""
        return self._vector_db.status

    def update_index(self) -> tuple[bool, str]:
        """ドキュメントフォルダのファイルをチャンク分割・ベクトル化してインデックスを更新する。

        Returns:
            (成功フラグ, メッセージ) のタプル
        """
        doc_dir: str = get_config("RAG_CHAT_DIR_PATH", "data/rag_chat")
        new_chunks: list[ChunkData] = []
        chunk_id: int = 0

        for filename in sorted(os.listdir(doc_dir)):
            filepath: str = os.path.join(doc_dir, filename)
            if not os.path.isfile(filepath):
                continue
            with open(filepath, encoding="utf-8") as f:
                content: str = f.read()

            for chunk_text in self._split_chunks(content):
                embedding: list[float] = self._gemini.embed(chunk_text)
                new_chunks.append({
                    "id": f"chunk_{chunk_id}",
                    "text": chunk_text,
                    "source": filename,
                    "embedding": embedding,
                })
                chunk_id += 1

        updated_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._vector_db.save(new_chunks, updated_at)
        return True, f"{len(new_chunks)}件のチャンクを更新しました"

    def _split_chunks(self, content: str) -> list[str]:
        """Q&A形式のテキストをQ&Aペア単位でチャンク分割する。"""
        chunks: list[str] = []
        current: list[str] = []
        for line in content.splitlines():
            if line.startswith("Q:") and current:
                chunk: str = "\n".join(current).strip()
                if chunk:
                    chunks.append(chunk)
                current = [line]
            else:
                current.append(line)
        if current:
            chunk = "\n".join(current).strip()
            if chunk:
                chunks.append(chunk)
        return chunks
