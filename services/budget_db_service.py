"""予算データのDB接続・取得・保存サービス。"""

import os

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

# Supabaseクライアントの初期化
_client: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)


def get_budgets(month: str) -> pd.DataFrame:
    """指定月の予算データをSupabaseから取得してDataFrameで返す。

    profit_marginはDB上では0.00形式（例: 0.13）で保存されているため、
    画面表示用に100倍して%値（例: 13.0）に変換して返す。
    """
    response = _client.table("budgets").select(
        "sales_rep, amount, profit_margin"
    ).eq("month", month).order("sales_rep").execute()

    df: pd.DataFrame = pd.DataFrame(response.data)
    if df.empty:
        # 空のときもカラム名を日本語で返す
        return pd.DataFrame(columns=["営業担当", "予算金額", "目標利益率"])

    # profit_marginを%値に変換（例: 0.13 → 13.0）
    df["profit_margin"] = (df["profit_margin"] * 100).round(2)

    # カラム名を日本語に変換
    df = df.rename(columns={
        "sales_rep":     "営業担当",
        "amount":        "予算金額",
        "profit_margin": "目標利益率",
    })
    return df


def save_budget(month: str, sales_rep: str, amount: int, target_margin: float) -> None:
    """月・営業担当の予算をSupabaseに保存する。既存データは上書きする。

    target_marginは画面上の%値（例: 13.0）を受け取り、
    DB保存時に0.00形式（例: 0.13）に変換する。
    """
    # %値を小数形式に変換（例: 13.0 → 0.13）
    profit_margin: float = round(target_margin / 100.0, 4)

    _client.table("budgets").upsert({
        "month":         month,
        "sales_rep":     sales_rep,
        "amount":        amount,
        "profit_margin": profit_margin,
    }, on_conflict="month,sales_rep").execute()
