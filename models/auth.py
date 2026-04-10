"""認証ユーザーのデータ構造。"""

from dataclasses import dataclass


@dataclass
class UserInfo:
    """Googleログインユーザーの情報を保持するデータクラス。"""

    id: str
    """GoogleユーザーID"""
    email: str
    """メールアドレス"""
    name: str
    """表示名"""
    avatar_url: str
    """プロフィール画像URL"""
