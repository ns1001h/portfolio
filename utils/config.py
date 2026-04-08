"""環境設定値の取得ユーティリティ。ローカルと Streamlit Cloud の両環境に対応する。"""

import os

import streamlit as st
from dotenv import load_dotenv

# ローカル開発時は .env から環境変数を読み込む
load_dotenv()


def get_config(key: str, default: str = "") -> str:
    """設定値を取得する。Streamlit Cloud では st.secrets を、ローカルでは os.getenv を使用する。

    優先順位: st.secrets → os.getenv → default

    Args:
        key: 設定キー名
        default: どちらにも存在しない場合のデフォルト値

    Returns:
        設定値の文字列
    """
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, default)
