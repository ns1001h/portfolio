# CLAUDE.md — プロジェクトルール

## プロジェクト概要
Streamlit + SQLite を使ったWebダッシュボードアプリ。

## フォルダ構成ルール

| フォルダ | 役割 |
|---|---|
| `services/` | 外部システムへの接続のみ（DB接続・API接続など） |
| `controllers/` | ビジネスロジック（サービスを組み合わせた処理） |
| `pages/` | Streamlit の画面・コンポーネント・イベント処理 |
| `models/` | データ構造（dataclassなど） |
| `utils/` | 共通ユーティリティ |
| `db/` | SQLite データベースファイル |
| ルート | `app.py` のみ（エントリーポイント） |

- 新しいDB接続・外部API接続 → `services/` に追加
- 複数のサービスを組み合わせるビジネスロジック → `controllers/` に追加
- 新しい画面・UIパーツ → `pages/` に追加
- データ構造の定義 → `models/` に追加
- 複数箇所で使う共通処理 → `utils/` に追加
- SQLite ファイル（`.db`）は `db/` に配置すること
- `app.py` にはロジックを書かない。初期化と起動のみ。

## 技術スタック
- Python / Streamlit（UIフレームワーク）
- SQLite（データベース）
- pandas（データ処理）
- plotly（グラフ描画）
- `python-dotenv`（`.env` で設定値管理）

## ファイル命名規則
- `pages/` のファイル名は `番号_スネークケース_page.py` の形式にすること（例: `1_dashboard_page.py`）
- `controllers/` のファイル名は `スネークケース_ctrl.py` の形式にすること（例: `dashboard_ctrl.py`）
- `services/` のファイル名は `スネークケース_service.py` の形式にすること（例: `sales_service.py`）

## コーディングルール
- Python の型アノテーションを必ず記述すること（変数・引数・戻り値すべて）
- VSCode の Pylance 型チェックは `basic` モードで運用
- コメントは日本語で記述すること
- ネストが深いコードは変数に切り出して読みやすくすること
- クラスには必ずdocstringで役割を記述すること
- 関数・メソッドには必ずdocstringで処理内容を記述すること

## セキュリティルール
- APIキー・設定値は必ず `.env` に記述すること
- ハードコーディング禁止（コード内に直接値を書かない）
- `.env` は `.gitignore` に追加し、リポジトリにコミットしない

## 環境変数（`.env`）
```
DB_PATH=...
```

## 作業ルール
- コードを変更したら最後に `python -c "import ..."` でインポートエラーがないか確認すること
- エラーが出た場合は自分で修正してから終了すること

## 実行方法
```bash
source .venv/bin/activate
streamlit run app.py
```
