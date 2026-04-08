"""Gemini API への接続を一元管理するサービス。"""

from google import genai
from google.genai import types

from utils.config import get_config


class GeminiService:
    """Gemini APIへの接続を一元管理するサービス。テキスト生成・ベクトル化を提供する。"""

    _client: genai.Client
    _model_id: str        # テキスト生成用モデルID
    _embed_model_id: str  # Embedding用モデルID

    def __init__(self) -> None:
        """環境変数からAPIキーとモデルIDを読み込み、Geminiクライアントを初期化する。"""
        api_key: str = get_config("GEMINI_API_KEY", "")
        self._model_id = get_config("GEMINI_MODEL_ID", "")
        self._embed_model_id = get_config("GEMINI_EMBED_MODEL_ID", "")

        if not api_key:
            raise ValueError(".envファイルに GEMINI_API_KEY が設定されていません")
        if not self._model_id:
            raise ValueError(".envファイルに GEMINI_MODEL_ID が設定されていません")

        # Geminiクライアントを初期化（全API呼び出しで共有）
        self._client = genai.Client(api_key=api_key)

    def generate(
        self,
        user_text: str,
        history: list[dict[str, str]] | None = None,
        system_instruction: str | None = None,
    ) -> str:
        """テキストを生成して返す。historyに会話履歴を渡すとマルチターン対話が可能。

        Args:
            user_text: ユーザーの入力テキスト
            history: 過去の会話履歴（{"role": "user"/"model", "text": "..."}のリスト）
            system_instruction: システム指示（機密情報保護ポリシーなどを含む）

        Returns:
            Geminiが生成した応答テキスト
        """
        # 会話履歴をGemini APIのContents形式に変換
        contents: list[types.Content] = []
        if history:
            for entry in history:
                role: str = entry["role"]
                text: str = entry["text"]
                contents.append(
                    types.Content(role=role, parts=[types.Part(text=text)])
                )

        # 最新のユーザーメッセージを追加
        contents.append(
            types.Content(role="user", parts=[types.Part(text=user_text)])
        )

        # システム指示が指定された場合はConfigに設定する
        config: types.GenerateContentConfig | None = None
        if system_instruction:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction
            )

        response = self._client.models.generate_content(
            model=self._model_id,
            contents=contents,
            config=config,
        )
        return response.text or ""

    def generate_with_system(self, user_text: str, system_instruction: str) -> str:
        """システム指示付きでテキストを生成して返す。RAGのプロンプト注入に使用する。

        Args:
            user_text: ユーザーの入力テキスト
            system_instruction: システム指示（FAQコンテキストなどを含む）

        Returns:
            Geminiが生成した応答テキスト
        """
        config: types.GenerateContentConfig = types.GenerateContentConfig(
            system_instruction=system_instruction
        )
        response = self._client.models.generate_content(
            model=self._model_id,
            contents=user_text,
            config=config,
        )
        return response.text or ""

    def embed(self, text: str) -> list[float]:
        """テキストをベクトル化して返す。FAQインデックス更新時に使用する。

        Args:
            text: ベクトル化するテキスト

        Returns:
            埋め込みベクトル（float のリスト）
        """
        if not self._embed_model_id:
            raise ValueError(".envファイルに GEMINI_EMBED_MODEL_ID が設定されていません")
        response = self._client.models.embed_content(
            model=self._embed_model_id,
            contents=text,
        )
        if not response.embeddings:
            return []
        values: list[float] | None = response.embeddings[0].values
        return values if values is not None else []
