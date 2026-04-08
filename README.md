# 業務効率化 AI ポートフォリオ

Python × Streamlit × Google Gemini × Supabase で構築した、社内業務効率化をテーマにした AI ポートフォリオアプリです。

## デモ

> Streamlit Cloud にデプロイ予定

---

## 機能一覧

### 🔒 セキュアAIチャット
機密情報漏洩対策を実装した企業向け AI チャット。

- **正規表現フィルタ（第一防衛線）**：電話番号・メールアドレス・マイナンバー・クレジットカード番号・銀行口座など 10 種類の個人情報を送信前に検出・ブロック
- **システムプロンプト（第二防衛線）**：AI 側にも機密情報を扱わないよう指示し、二重防御を実現

### 🤖 社内RAGチャット
社内規定・FAQ ドキュメントを AI が検索して回答する RAG システム。

- ドキュメントをチャンク分割してベクトル化し Supabase に保存
- クエリとのコサイン類似度で関連チャンクを検索してから Gemini に回答生成させる RAG 構成
- 管理画面からドキュメントのアップロード・インデックス更新が可能

### 🚚 引越し見積もり
過去の案件データをベクトル DB に蓄積し、類似案件から見積もりを自動算出する RAG 応用デモ。

- Gemini が自然言語の入力から荷物の体積・移動距離を推定
- 正規化ユークリッド距離で類似案件を検索し、コストを加重平均で算出
- 管理画面から CSV インポート・利益率・季節係数の設定が可能

### 📊 経営ダッシュボード
売上・利益・予算達成率をリアルタイムで可視化。

- 月次 KPI（売上・利益・利益率・案件数）をカード表示
- 売上・利益の予算達成率をゲージチャートで表示
- サービス別・顧客別・営業担当別の受注金額をバーチャートで集計

---

## 技術スタック

| 分類 | 技術 |
|---|---|
| 言語 | Python 3.14 |
| UI フレームワーク | Streamlit |
| AI / 埋め込み | Google Gemini API（gemini-2.5-flash / gemini-embedding-001） |
| データベース | SQLite（業務データ）/ Supabase PostgreSQL + pgvector（ベクトルDB） |
| データ処理 | pandas |
| グラフ描画 | Plotly |
| 設定管理 | python-dotenv / Streamlit Secrets |

---

## フォルダ構成

```
streamlit_app/
├── app.py                  # エントリーポイント
├── pages/                  # 各画面
├── controllers/            # ビジネスロジック
├── services/               # 外部システム接続（DB・API）
├── models/                 # データ構造（dataclass）
├── utils/                  # 共通ユーティリティ
├── prompt/                 # システムプロンプト
├── data/                   # RAGチャット用ドキュメント
└── db/                     # SQLite ファイル
```

---

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env` ファイルをプロジェクトルートに作成し、以下を設定してください。

```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# Gemini API
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_ID=models/gemini-2.5-flash
GEMINI_EMBED_MODEL_ID=models/gemini-embedding-001

# 引越し見積もり
MOVE_EST_SEARCH_N_RESULTS=3
MOVE_EST_SEARCH_MAX_DISTANCE=0.6
MOVE_EST_VOLUME_PROMPT_PATH=prompt/move_est_volume.txt
MOVE_EST_DISTANCE_PROMPT_PATH=prompt/move_est_distance.txt

# セキュアAIチャット
SECURE_CHAT_PROMPT_PATH=prompt/secure_chat.txt

# 社内RAGチャット
RAG_CHAT_SEARCH_N_RESULTS=5
RAG_CHAT_SEARCH_MIN_SCORE=0.5
RAG_CHAT_PROMPT_PATH=prompt/rag_chat.txt
RAG_CHAT_DIR_PATH=data/rag_chat
```

### 3. Supabase のテーブル作成

Supabase の SQL Editor で以下を実行してください。

```sql
-- pgvector 拡張を有効化
create extension if not exists vector;

-- 社内RAGチャット用チャンクテーブル
create table rag_chat_chunks (
  id text primary key,
  text text,
  source text,
  embedding vector(3072),
  updated_at text
);

-- 引越し見積もり用テーブル（既存の move_est_cases に embedding カラムを追加）
alter table move_est_cases add column embedding vector(3072);
```

### 4. アプリの起動

```bash
source .venv/bin/activate
streamlit run app.py
```

---

## Streamlit Cloud へのデプロイ

`.env` の代わりに Streamlit Cloud の **Secrets** に同じキーを設定することで動作します。`utils/config.py` の `get_config()` が自動的に切り替えます。
