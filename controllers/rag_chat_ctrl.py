"""社内RAGチャットのビジネスロジックを担うコントローラー。"""

from services.gemini_service import GeminiService
from services.rag_chat_vector_db_service import RagChatVectorDbService
from utils.config import get_config


class RagChatCtrl:
    """社内RAGチャットのビジネスロジックを担うコントローラー。RAG回答生成を提供する。"""

    _gemini: GeminiService
    _vector_db: RagChatVectorDbService

    def __init__(self, gemini: GeminiService, vector_db: RagChatVectorDbService) -> None:
        """GeminiServiceとRagChatVectorDbServiceを受け取って保持する。"""
        self._gemini = gemini
        self._vector_db = vector_db

    def get_response(self, user_text: str) -> tuple[str, str]:
        """質問に関連するドキュメントをベクトル検索してGeminiに回答させる。

        Args:
            user_text: ユーザーの質問テキスト

        Returns:
            (回答テキスト, デバッグ情報テキスト) のタプル
        """
        debug_lines: list[str] = []

        # 質問をベクトル化してDBを検索
        query_embedding: list[float] = self._gemini.embed(user_text)
        results: list[tuple[float, str, str]] = self._vector_db.search(query_embedding)

        if not results:
            debug_lines.append("検索結果：0件（ドキュメントが未更新またはスコア閾値以下）")
            return "ドキュメントが未更新です。管理ページからドキュメントを更新してください。", "\n".join(debug_lines)

        hit_lines: list[str] = [f"[{score:.3f}] {source}" for score, _, source in results]
        debug_lines.append(f"検索結果（{len(results)}件）:\n" + "\n".join(hit_lines))

        # 検索結果をファイル名ヘッダー付きでコンテキスト文字列に組み立てる
        context_parts: list[str] = [
            f"=== {source} ===\n{text}" for _, text, source in results
        ]
        doc_content: str = "\n\n".join(context_parts)

        # プロンプトにドキュメント内容を差し込んでGeminiに送信
        prompt_template: str = self._load_prompt_template()
        system_instruction: str = prompt_template.format(faq_content=doc_content)
        debug_lines.append(f"システム指示（抜粋）:\n{system_instruction[:200]}...")

        response: str = self._gemini.generate_with_system(user_text, system_instruction)
        return response, "\n\n".join(debug_lines)

    def _load_prompt_template(self) -> str:
        """環境変数で指定されたファイルからプロンプトテンプレートを読み込む。"""
        prompt_path: str = get_config("RAG_CHAT_PROMPT_PATH", "prompt/rag_chat.txt")
        with open(prompt_path, encoding="utf-8") as f:
            return f.read()
