"""데이터 처리부: 형식 검사 → 코일 전환 감지 → 판정 → 경고(중복 방지). 화면 코드와 분리된 순수 로직."""
from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from datetime import datetime

import config

logger = logging.getLogger(__name__)

COIL_NO_PATTERN = re.compile(r"^[A-Z]{3}[0-9]{4}$")
STEEL_GRADE_PATTERN = re.compile(r"^[A-Z]+$")


def evaluate(weight: float, upper: float = config.UPPER, lower: float = config.LOWER) -> str:
    """도금량 판정 (PRD 6장). 정확히 하한값·상한값은 정상이다."""
    if weight > upper:
        return "HIGH"
    if weight < lower:
        return "LOW"
    return "NORMAL"


def validate_record(record) -> str | None:
    """레코드 형식 검사 (FR-1). 문제가 있으면 이유, 없으면 None."""
    if not isinstance(record, dict):
        return "레코드가 객체가 아님"
    coil_no = record.get("coil_no")
    steel_grade = record.get("steel_grade")
    position = record.get("position")
    weight = record.get("coating_weight")
    if not isinstance(coil_no, str) or not COIL_NO_PATTERN.match(coil_no):
        return "coil_no 형식 오류 (영문 대문자 3자리 + 숫자 4자리)"
    if not isinstance(steel_grade, str) or not STEEL_GRADE_PATTERN.match(steel_grade):
        return "steel_grade 형식 오류 (영문 대문자)"
    if isinstance(position, bool) or not isinstance(position, int) or position < 0:
        return "position 형식 오류 (0 이상 정수)"
    if isinstance(weight, bool) or not isinstance(weight, (int, float)) or not math.isfinite(weight):
        return "coating_weight 형식 오류 (숫자)"
    return None


@dataclass
class Alert:
    type: str  # 'HIGH' | 'LOW'
    coil_no: str
    steel_grade: str
    position: int
    weight: float
    occurred_at: datetime


@dataclass
class Processor:
    """현재 코일의 그래프 데이터와 경고 상태를 가진다. 이전 코일 데이터는 보관하지 않는다 (FR-4.3)."""
    coil_no: str | None = None
    last_status: str = "NORMAL"
    alert_count: int = 0
    coil_change_count: int = 0
    positions: list[int] = field(default_factory=list)
    weights: list[float] = field(default_factory=list)
    statuses: list[str] = field(default_factory=list)
    latest: dict | None = None
    latest_status: str | None = None

    def process(self, record) -> Alert | None:
        """레코드 1건을 처리하고, 새 경고가 발생하면 Alert를 반환한다."""
        error = validate_record(record)
        if error:
            logger.warning("잘못된 레코드를 무시합니다: %s %r", error, record)
            return None

        if record["coil_no"] != self.coil_no:
            if self.coil_no is not None:
                self.coil_change_count += 1
            self.coil_no = record["coil_no"]
            self.last_status = "NORMAL"  # 코일이 바뀌면 중복 방지 상태 초기화 (FR-4.2)
            self.positions, self.weights, self.statuses = [], [], []

        status = evaluate(record["coating_weight"])
        self.positions.append(record["position"])
        self.weights.append(record["coating_weight"])
        self.statuses.append(status)
        self.latest, self.latest_status = record, status

        # 같은 종류의 이탈이 이어지면 처음 한 번만. 종류가 바뀌거나 정상 복귀 후 재이탈이면 새 경고 (FR-5.5)
        alert = None
        if status != "NORMAL" and status != self.last_status:
            self.alert_count += 1
            alert = Alert(status, record["coil_no"], record["steel_grade"], record["position"],
                          record["coating_weight"], datetime.now())
        self.last_status = status
        return alert
