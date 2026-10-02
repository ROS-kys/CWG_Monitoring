# 도금량 실시간 모니터링 (Streamlit)

도금량계 데이터(현재는 더미 데이터)를 받아 코일별 **위치[m] - 도금량[g/m²]** 그래프를 실시간으로 그리고, 도금량이 상한(90)을 넘거나 하한(80) 미만으로 떨어지면 경고창을 띄우는 앱입니다.

## 로컬 실행

이 폴더(저장소 루트)에서 실행합니다.

```
pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/app.py
```

## Streamlit Community Cloud 배포

1. 이 폴더 내용을 GitHub 저장소에 올립니다.
2. https://share.streamlit.io 에서 **Create app** → 저장소·브랜치 선택
3. **Main file path**: `streamlit_app/app.py`
4. **Advanced settings** → Python 3.12 또는 3.13
5. **Deploy**

## 구성

| 경로 | 내용 |
|---|---|
| `streamlit_app/app.py` | 화면 (정보 카드, 그래프, 경고창, 재생 제어) |
| `streamlit_app/processor.py` | 형식 검사 · 판정 · 경고 중복 방지 · 코일 전환 |
| `streamlit_app/config.py` | 기준값(목표 80, 상한 90, 하한 80), 단위, 재생 속도(초당 10 m) |
| `streamlit_app/requirements.txt` | 패키지 목록 |
| `data/dummy_data.json` | 더미 데이터 (코일 20개, 길이 800~1400 m) |
| `.streamlit/config.toml` | 어두운 테마 |
