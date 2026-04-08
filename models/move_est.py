"""引越し見積もりで使うデータ構造の定義。"""

from dataclasses import dataclass, field


@dataclass
class PastCase:
    """過去の引越し案件データ。体積・距離・費用・埋め込みベクトルを保持する。"""

    id: str                                               # 案件ID（例：case_001）
    volume_m3: float                                      # 荷物体積（m³）
    distance_km: float                                    # 移動距離（km）
    cost: int                                             # 実際の引越し費用（円、税込）
    embedding: list[float] = field(default_factory=list) # ベクトル埋め込み（検索用）


@dataclass
class MoveEstResult:
    """見積もり算出結果。入力値・類似案件・算出過程・最終見積もりをまとめて保持する。"""

    volume_m3: float               # 推定荷物体積（m³）
    distance_km: float             # 推定移動距離（km）
    similar_cases: list[PastCase]  # ベクトル検索で見つかった類似案件リスト
    base_cost: int                 # 参考原価（類似案件の加重平均費用、円）
    season_factor: float           # 季節係数（引越しシーズンの需要倍率）
    profit_rate: float             # 利益率（0〜1）
    estimate: int                  # 最終見積もり金額（円）
    debug_logs: list[str] = field(default_factory=list)  # デバッグログ
