"""機密情報検出結果のデータモデル。"""

from dataclasses import dataclass, field


@dataclass
class PiiDetectionResult:
    """PII（個人情報・機密情報）検出結果を保持するデータクラス。

    Attributes:
        has_pii: 機密情報が検出されたかどうか
        detected_types: 検出された機密情報の種類のリスト（例: ["電話番号", "メールアドレス"]）
        masked_text: 機密情報をマスクした表示用テキスト
    """

    has_pii: bool
    detected_types: list[str] = field(default_factory=list)
    masked_text: str = ""
