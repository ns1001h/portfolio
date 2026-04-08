"""セキュアAIチャットのビジネスロジックを担うコントローラー。"""

from models.pii_detection import PiiDetectionResult
from services.gemini_service import GeminiService
from utils.config import get_config
from utils.pii_detector import PiiDetector


def _load_security_prompt() -> str:
    """環境変数で指定されたファイルからセキュリティ用システムプロンプトを読み込む。

    Returns:
        プロンプトテキスト
    """
    prompt_path: str = get_config("SECURE_CHAT_PROMPT_PATH", "prompt/secure_chat.txt")
    with open(prompt_path, encoding="utf-8") as f:
        return f.read()


class SecureChatCtrl:
    """セキュアAIチャットのビジネスロジックを担うコントローラー。

    送信前にPIIフィルタ（第1防衛線）でブロックし、
    AIのシステムプロンプト（第2防衛線）でも機密情報への対応を指示する二重防御を実装する。
    """

    _gemini: GeminiService
    _pii_detector: PiiDetector

    def __init__(self, gemini: GeminiService) -> None:
        """GeminiServiceとPiiDetectorを初期化する。"""
        self._gemini = gemini
        self._pii_detector = PiiDetector()

    def check_pii(self, user_text: str) -> PiiDetectionResult:
        """入力テキストの機密情報チェックのみを行う（送信は行わない）。

        Args:
            user_text: ユーザーの入力テキスト

        Returns:
            PiiDetectionResult: 検出結果
        """
        return self._pii_detector.detect(user_text)

    def send_message(self, user_text: str, history: list[dict[str, str]]) -> str:
        """ユーザーのメッセージをGeminiに送信して回答を返す。

        【第1防衛線】送信前にPIIフィルタで機密情報を検出し、
        検出された場合はAPIに送信せずブロックする。
        【第2防衛線】システムプロンプトでAIにも機密情報対応を指示する。

        Args:
            user_text: ユーザーの入力テキスト
            history: 過去の会話履歴（{"role": "user"/"model", "text": "..."}のリスト）

        Returns:
            Geminiが生成した応答テキスト

        Raises:
            ValueError: 機密情報が検出された場合（APIには送信しない）
        """
        # 第1防衛線: 正規表現による機密情報チェック
        result: PiiDetectionResult = self._pii_detector.detect(user_text)
        if result.has_pii:
            types_str: str = "、".join(result.detected_types)
            raise ValueError(f"機密情報が検出されました: {types_str}")

        # 第2防衛線: システムプロンプト付きで送信
        return self._gemini.generate(
            user_text,
            history=history,
            system_instruction=_load_security_prompt(),
        )
