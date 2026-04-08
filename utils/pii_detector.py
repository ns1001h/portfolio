"""個人情報・機密情報（PII）を検出・マスクするユーティリティ。"""

import re

from models.pii_detection import PiiDetectionResult

# 検出パターン定義: (種類名, 正規表現パターン, マスク文字列)
_PII_PATTERNS: list[tuple[str, str, str]] = [
    # 電話番号（固定電話・携帯・ハイフンあり/なし）
    (
        "電話番号",
        r"(?<!\d)0\d{1,4}[-\u2010\u2011\u2012\u2013\u2014\uff0d]?\d{1,4}[-\u2010\u2011\u2012\u2013\u2014\uff0d]?\d{4}(?!\d)",
        "[電話番号]",
    ),
    # メールアドレス
    (
        "メールアドレス",
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
        "[メールアドレス]",
    ),
    # マイナンバー（12桁数字、前後に数字がないもの）
    (
        "マイナンバー",
        r"(?<!\d)\d{12}(?!\d)",
        "[マイナンバー]",
    ),
    # クレジットカード番号（16桁、ハイフン・スペース区切り可）
    (
        "クレジットカード番号",
        r"(?<!\d)\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)",
        "[クレジットカード番号]",
    ),
    # 郵便番号（〒付きまたはハイフンあり）
    (
        "郵便番号",
        r"(?:〒|\bT)?\d{3}[-\uff0d]\d{4}",
        "[郵便番号]",
    ),
    # 銀行口座番号（支店3桁＋口座7桁 or 単独7桁）
    (
        "銀行口座番号",
        r"(?<!\d)\d{3,4}[-\s]?\d{7}(?!\d)",
        "[口座番号]",
    ),
    # 顧客ID（C-またはCUST-で始まる英数字）
    (
        "顧客ID",
        r"\b(?:C|CUST|CID)[-_]?\d{4,10}\b",
        "[顧客ID]",
    ),
    # 社員番号（E-またはEMP-で始まる英数字）
    (
        "社員番号",
        r"\b(?:E|EMP)[-_]?\d{4,10}\b",
        "[社員番号]",
    ),
    # 氏名パターン（【氏名】または[氏名]で明示された箇所）
    (
        "氏名",
        r"(?:【氏名】|\[氏名\])[^\s\u3000【\[]{2,10}",
        "[氏名]",
    ),
    # IPアドレス（内部ネットワーク情報として）
    (
        "IPアドレス",
        r"\b(?:192\.168|10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b",
        "[IPアドレス]",
    ),
]


class PiiDetector:
    """テキスト中の個人情報・機密情報を検出・マスクするクラス。

    正規表現パターンにより以下の情報を検出する:
    電話番号、メールアドレス、マイナンバー、クレジットカード番号、
    郵便番号、銀行口座番号、顧客ID、社員番号、氏名、IPアドレス
    """

    def detect(self, text: str) -> PiiDetectionResult:
        """テキストを検査し、機密情報の検出結果を返す。

        Args:
            text: 検査対象のテキスト

        Returns:
            PiiDetectionResult: 検出有無・種類・マスク済みテキストを含む結果
        """
        detected_types: list[str] = []
        masked_text: str = text

        for pii_type, pattern, mask in _PII_PATTERNS:
            compiled: re.Pattern[str] = re.compile(pattern, re.IGNORECASE)
            if compiled.search(masked_text):
                detected_types.append(pii_type)
                masked_text = compiled.sub(mask, masked_text)

        return PiiDetectionResult(
            has_pii=len(detected_types) > 0,
            detected_types=detected_types,
            masked_text=masked_text,
        )
