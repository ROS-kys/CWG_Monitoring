"""앱 전체 설정값 (PRD 6장). 웹앱의 js/config.js와 같은 값을 유지한다."""
from pathlib import Path

# 기준값
TARGET = 80  # 목표 도금량
UPPER = 90   # 상한: 이 값을 초과하면 상한 경고
LOWER = 80   # 하한: 이 값 미만이면 하한 경고

# 도금량 데이터 범위 = 그래프 Y축 범위
VALUE_MIN = 70
VALUE_MAX = 110

DECIMALS = 2
UNIT = "g/m²"

# 재생: 레코드 1건 = 1 m. ×1 속도 = 초당 10 m
METERS_PER_SECOND = 10
SPEEDS = [1, 2, 5]
REFRESH_SECONDS = 0.5           # 재생 중 화면 갱신 주기
MAX_RECORDS_PER_REFRESH = 500   # 한 번에 따라잡는 최대 건수 (화면 멈춤 방지)

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "dummy_data.json"
