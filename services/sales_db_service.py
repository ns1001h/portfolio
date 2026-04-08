"""案件データのDB接続・取得サービス。"""

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


def get_deals() -> pd.DataFrame:
    """案件データをSupabaseから取得してDataFrameで返す。"""
    response = _client.table("deals").select(
        "customer, deal_name, sales_rep, service, date, amount, cost"
    ).order("date").execute()

    df: pd.DataFrame = pd.DataFrame(response.data)
    if df.empty:
        return df

    # カラム名を日本語に変換
    df = df.rename(columns={
        "customer":  "顧客",
        "deal_name": "案件",
        "sales_rep": "営業担当",
        "service":   "サービス",
        "date":      "日付",
        "amount":    "金額",
        "cost":      "原価",
    })
    return df
