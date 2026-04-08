"""引越し見積もり算出のビジネスロジックを担うコントローラー。"""

from models.move_est import MoveEstResult, PastCase
from services.gemini_service import GeminiService
from services.move_est_db_service import MoveEstDbService
from services.move_est_vector_db_service import MoveEstVectorDbService
from utils.config import get_config


class MoveEstCtrl:
    """引越し見積もり算出のビジネスロジックを担うコントローラー。体積・距離をGeminiで推定し類似案件から見積もりを算出する。"""

    _gemini: GeminiService
    _vector_db: MoveEstVectorDbService
    _db: MoveEstDbService
    _volume_prompt: str   # 荷物体積推定用システム指示
    _distance_prompt: str # 移動距離推定用システム指示

    def __init__(
        self,
        gemini: GeminiService,
        vector_db: MoveEstVectorDbService,
        db: MoveEstDbService,
    ) -> None:
        """サービスを受け取り、環境変数からプロンプトを読み込む。"""
        self._gemini = gemini
        self._vector_db = vector_db
        self._db = db

        volume_path: str = get_config("MOVE_EST_VOLUME_PROMPT_PATH", "prompt/move_est_volume.txt")
        with open(volume_path, encoding="utf-8") as f:
            self._volume_prompt = f.read()

        distance_path: str = get_config("MOVE_EST_DISTANCE_PROMPT_PATH", "prompt/move_est_distance.txt")
        with open(distance_path, encoding="utf-8") as f:
            self._distance_prompt = f.read()

    def get_estimate(
        self,
        move_date: str,
        from_pref: str,
        to_pref: str,
        furniture: list[str],
    ) -> MoveEstResult:
        """引越し情報から見積もりを算出して返す。

        Args:
            move_date: 引越し予定日（YYYY-MM-DD形式）
            from_pref: 出発都道府県名
            to_pref: 目的都道府県名
            furniture: 荷物・家具リスト

        Returns:
            MoveEstResult: 見積もり算出結果
        """
        debug_logs: list[str] = []
        debug_mode: bool = get_config("DEBUG_MODE", "0") == "1"

        # STEP1: 荷物の合計体積をGeminiで推定する
        volume_m3: float = self._get_volume(furniture, debug_logs, debug_mode)

        # STEP2: 移動距離をGeminiで推定する
        distance_km: float = self._get_distance(from_pref, to_pref, debug_logs, debug_mode)

        # STEP3: 体積・距離をもとにベクトルDBを検索して類似案件を取得する
        if debug_mode:
            debug_logs.append(f"【STEP3】類似案件検索\n体積：{volume_m3:.1f}m³ 距離：{distance_km:.0f}km")
        search_results: list[tuple[float, PastCase]] = self._vector_db.search(volume_m3, distance_km)

        if debug_mode:
            if search_results:
                case_lines: list[str] = [
                    f"  {c.id}：体積{c.volume_m3}m³ 距離{c.distance_km}km 費用{c.cost:,}円　距離={dist:.3f}"
                    for dist, c in search_results
                ]
                debug_logs.append(f"【STEP3】検索結果（{len(search_results)}件）\n" + "\n".join(case_lines))
            else:
                debug_logs.append("【STEP3】検索結果：0件")

        if not search_results:
            raise ValueError("類似案件が見つかりませんでした。条件を変えるかデータを更新してください。")

        # 距離の近さを重みにした加重平均で参考原価を算出する
        epsilon: float = 1e-6
        weights: list[float] = [1.0 / (dist + epsilon) for dist, _ in search_results]
        base_cost: int = int(
            sum(w * c.cost for w, (_, c) in zip(weights, search_results)) / sum(weights)
        )
        similar_cases: list[PastCase] = [c for _, c in search_results]

        if debug_mode:
            weight_lines: list[str] = [
                f"  {c.id}：費用{c.cost:,}円 × 重み{w:.3f}"
                for w, (_, c) in zip(weights, search_results)
            ]
            debug_logs.append(
                "【STEP3】加重平均の計算\n" + "\n".join(weight_lines) +
                f"\n  → 参考原価：{base_cost:,}円"
            )

        # STEP4: 季節係数・利益率をDBから取得して見積もり金額を算出する
        month: int = int(move_date.split("-")[1])
        season_factors: list[float] = self._db.get_season_factors()
        season_factor: float = season_factors[month - 1]
        profit_rate: float = self._db.get_profit_rate()
        estimate: int = int(base_cost * season_factor / (1 - profit_rate))

        if debug_mode:
            debug_logs.append(
                f"【STEP4】見積もり算出\n"
                f"  参考原価：{base_cost:,}円\n"
                f"  季節係数：{season_factor}（{month}月）\n"
                f"  利益率：{int(profit_rate * 100)}%\n"
                f"  計算式：{base_cost:,} × {season_factor} ÷ (1 - {profit_rate}) = {estimate:,}円"
            )

        return MoveEstResult(
            volume_m3=volume_m3,
            distance_km=distance_km,
            similar_cases=similar_cases,
            base_cost=base_cost,
            season_factor=season_factor,
            profit_rate=profit_rate,
            estimate=estimate,
            debug_logs=debug_logs,
        )

    def _get_volume(self, furniture: list[str], debug_logs: list[str], debug_mode: bool) -> float:
        """家具・荷物リストからGeminiを使って合計体積（m³）を推定して返す。"""
        furniture_text: str = "\n".join(f"・{item}" for item in furniture)
        if debug_mode:
            debug_logs.append(f"【STEP1】体積推定\nシステム指示：{self._volume_prompt}\n入力：\n{furniture_text}")
        response: str = self._gemini.generate_with_system(furniture_text, self._volume_prompt)
        if debug_mode:
            debug_logs.append(f"【STEP1】体積推定 結果\n{response.strip()}")
        try:
            return float(response.strip())
        except ValueError:
            raise ValueError(f"体積の推定結果を数値に変換できませんでした：{response}")

    def _get_distance(self, from_pref: str, to_pref: str, debug_logs: list[str], debug_mode: bool) -> float:
        """出発地・目的地からGeminiを使って移動距離（km）を推定して返す。"""
        route_text: str = f"{from_pref}から{to_pref}"
        if debug_mode:
            debug_logs.append(f"【STEP2】距離推定\nシステム指示：{self._distance_prompt}\n入力：{route_text}")
        response: str = self._gemini.generate_with_system(route_text, self._distance_prompt)
        if debug_mode:
            debug_logs.append(f"【STEP2】距離推定 結果\n{response.strip()}")
        try:
            return float(response.strip())
        except ValueError:
            raise ValueError(f"移動距離の推定結果を数値に変換できませんでした：{response}")
