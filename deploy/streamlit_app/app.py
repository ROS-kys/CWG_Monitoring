"""도금량 실시간 모니터링 — Streamlit 버전.

실행: streamlit run app.py   (streamlit_app 폴더에서)
"""
from __future__ import annotations

import json
import time

import plotly.graph_objects as go
import streamlit as st

import config
from processor import Alert, Processor

st.set_page_config(page_title="도금량 실시간 모니터링", page_icon="📈", layout="wide")

COLORS = {
    "series": "#3987e5",
    "grid": "#2c2c2a",
    "axis": "#383835",
    "band": "rgba(12,163,12,0.08)",
    "surface": "#1a1a19",
    "text": "#ffffff",
    "text2": "#c3c2b7",
    "muted": "#898781",
    "NORMAL": "#0ca30c",
    "HIGH": "#d03b3b",
    "LOW": "#fab219",
}
STATUS_LABELS = {"NORMAL": "정상", "HIGH": "상한 초과", "LOW": "하한 이탈"}
STATUS_ICONS = {"NORMAL": "●", "HIGH": "▲", "LOW": "▼"}
PLAYBACK_LABELS = {"idle": "대기", "playing": "재생 중", "paused": "일시정지", "ended": "재생 완료", "error": "데이터 없음"}
ALERT_TEXT = {
    "HIGH": ("도금량 상한 초과", f"도금량이 상한({config.UPPER})을 초과했습니다."),
    "LOW": ("도금량 하한 이탈", f"도금량이 하한({config.LOWER}) 미만으로 떨어졌습니다."),
}

CSS = f"""
<style>
  .block-container {{ padding-top: 1.2rem; padding-bottom: 0.5rem; max-width: 100%; }}
  [data-testid="stHeader"] {{ background: transparent; }}
  .num {{ font-variant-numeric: tabular-nums; }}
  h1.app-title {{ font-size: 1.6rem; font-weight: 700; margin: 0; padding: 0.4rem 0; }}

  .cards {{ display: grid; grid-template-columns: 1.25fr 1fr 1fr 1.35fr; gap: 16px; }}
  .card {{ background: {COLORS['surface']}; border: 1px solid rgba(255,255,255,.10);
           border-left: 4px solid rgba(255,255,255,.18); border-radius: 10px; padding: 14px 20px; min-width: 0; }}
  .card.primary {{ border-left-color: {COLORS['series']}; }}
  .card.NORMAL {{ border-left-color: {COLORS['NORMAL']}; }}
  .card.HIGH {{ border-left-color: {COLORS['HIGH']}; }}
  .card.LOW {{ border-left-color: {COLORS['LOW']}; }}
  .card-label {{ color: {COLORS['muted']}; font-size: .95rem; font-weight: 600; }}
  .card-value {{ font-size: 2.2rem; font-weight: 700; line-height: 1.2; white-space: nowrap;
                 overflow: hidden; text-overflow: ellipsis; }}
  .card.primary .card-value {{ font-size: 3rem; letter-spacing: .02em; }}
  .unit {{ margin-left: .3em; color: {COLORS['text2']}; font-size: .45em; font-weight: 600; }}
  .badge {{ display: inline-block; margin-left: 12px; padding: 3px 12px; border-radius: 999px;
            font-size: 1.05rem; font-weight: 700; vertical-align: middle; }}
  .badge.NORMAL {{ background: {COLORS['NORMAL']}; color: #0b0b0b; }}
  .badge.HIGH {{ background: {COLORS['HIGH']}; color: #fff; }}
  .badge.LOW {{ background: {COLORS['LOW']}; color: #0b0b0b; }}

  .statusbar {{ display: flex; justify-content: space-between; color: {COLORS['text2']}; font-size: 1rem; }}
  .statusbar b {{ color: {COLORS['text']}; margin-left: 6px; }}
  .dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; background: {COLORS['muted']}; }}
  .dot.playing {{ background: {COLORS['NORMAL']}; }}
  .dot.paused {{ background: {COLORS['LOW']}; }}
  .dot.ended {{ background: {COLORS['series']}; }}
  .dot.error {{ background: {COLORS['HIGH']}; }}

  /* 경고창: 화면 중앙 고정 모달 + 반투명 배경 */
  .alert-backdrop {{ position: fixed; inset: 0; background: rgba(0,0,0,.62); z-index: 999990; }}
  .st-key-alert_high, .st-key-alert_low {{ position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
      z-index: 999991; width: min(520px, 92vw); background: {COLORS['surface']}; border-radius: 14px;
      border: 3px solid var(--tone); box-shadow: 0 24px 60px rgba(0,0,0,.6); padding: 0 24px 22px; gap: 0; }}
  .st-key-alert_high {{ --tone: {COLORS['HIGH']}; --on-tone: #fff; }}
  .st-key-alert_low {{ --tone: {COLORS['LOW']}; --on-tone: #0b0b0b; }}
  .alert-head {{ margin: 0 -24px; padding: 14px 24px; background: var(--tone); color: var(--on-tone);
                 font-size: 1.6rem; font-weight: 800; border-radius: 10px 10px 0 0; }}
  .alert-msg {{ margin: 18px 0 0; color: {COLORS['text2']}; font-size: 1.1rem; }}
  .alert-value {{ margin: 14px 0 0; padding: 12px; text-align: center; background: #0f1011;
                  border: 1px solid rgba(255,255,255,.10); border-radius: 10px; }}
  .alert-value small {{ display: block; color: {COLORS['muted']}; font-weight: 600; }}
  .alert-value strong {{ font-size: 4rem; font-weight: 800; line-height: 1.1; }}
  .alert-value .unit {{ font-size: 1.4rem; }}
  .alert-details {{ display: grid; grid-template-columns: auto 1fr; gap: 6px 20px; margin: 16px 0 18px; font-size: 1.1rem; }}
  .alert-details span:nth-child(odd) {{ color: {COLORS['muted']}; font-weight: 600; }}
  .alert-details span:nth-child(even) {{ font-weight: 700; }}
  .st-key-alert_high button, .st-key-alert_low button {{ min-height: 56px; background: var(--tone) !important;
      border-color: var(--tone) !important; color: var(--on-tone) !important; }}
  .st-key-alert_high button p, .st-key-alert_low button p {{ font-size: 1.25rem; font-weight: 700; }}
</style>
"""


@st.cache_data
def load_records() -> list[dict]:
    with open(config.DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def init_state() -> None:
    ss = st.session_state
    if "processor" in ss:
        return
    ss.processor = Processor()
    ss.index = 0
    ss.state = "idle"
    ss.speed = 1
    ss.anchor_time = 0.0
    ss.anchor_index = 0
    ss.alert = None  # 화면에 떠 있는 경고 (Alert)


# ── 재생 제어 ──────────────────────────────────────────────

def anchor() -> None:
    """재생(재개·속도 변경) 기준 시각과 위치를 다시 잡는다."""
    st.session_state.anchor_time = time.monotonic()
    st.session_state.anchor_index = st.session_state.index


def reset_all() -> None:
    ss = st.session_state
    ss.processor = Processor()
    ss.index = 0
    ss.state = "idle"
    ss.alert = None


def on_start() -> None:
    if st.session_state.state in ("idle", "paused"):
        anchor()
        st.session_state.state = "playing"


def on_pause() -> None:
    if st.session_state.state == "playing":
        advance(load_records())  # 멈추기 직전까지 밀린 레코드를 반영
        st.session_state.state = "paused"


def on_restart() -> None:
    reset_all()
    on_start()


def on_speed_change() -> None:
    if st.session_state.state == "playing":
        advance(load_records())
    st.session_state.speed = st.session_state.speed_select
    anchor()


def on_confirm_alert() -> None:
    st.session_state.alert = None


def advance(records: list[dict]) -> None:
    """경과 시간 기준으로 재생해야 할 레코드를 모두 처리한다 (초당 10 m × 속도)."""
    ss = st.session_state
    if ss.state != "playing":
        return
    rate = config.METERS_PER_SECOND * ss.speed  # 레코드 1건 = 1 m
    due = ss.anchor_index + int((time.monotonic() - ss.anchor_time) * rate)
    target = min(due, ss.index + config.MAX_RECORDS_PER_REFRESH, len(records))
    while ss.index < target:
        alert = ss.processor.process(records[ss.index])
        ss.index += 1
        if alert:
            ss.alert = alert  # 떠 있는 경고창은 최신 경고로 바뀐다 (FR-5.7)
    if ss.index >= len(records):
        ss.state = "ended"


def progress(records: list[dict]) -> tuple[int, int]:
    """(현재 코일 순번, 전체 코일 수)"""
    coil_order = list(dict.fromkeys(r["coil_no"] for r in records))
    current = st.session_state.processor.coil_no
    return (coil_order.index(current) + 1 if current in coil_order else 0), len(coil_order)


# ── 화면 ──────────────────────────────────────────────────

def fmt(weight: float) -> str:
    return f"{weight:.{config.DECIMALS}f}"


def render_cards(p: Processor) -> None:
    r, status = p.latest, p.latest_status
    unit = f'<span class="unit">{config.UNIT}</span>' if r else ""
    badge = f'<span class="badge {status}">{STATUS_ICONS[status]} {STATUS_LABELS[status]}</span>' if r else ""
    st.markdown(
        f"""<div class="cards">
          <div class="card primary"><div class="card-label">코일번호</div><div class="card-value">{r['coil_no'] if r else '-'}</div></div>
          <div class="card primary"><div class="card-label">강종</div><div class="card-value">{r['steel_grade'] if r else '-'}</div></div>
          <div class="card"><div class="card-label">현재 위치</div><div class="card-value num">{f"{r['position']} m" if r else '-'}</div></div>
          <div class="card {status or ''}"><div class="card-label">현재 도금량</div>
            <div class="card-value num">{fmt(r['coating_weight']) if r else '-'}{unit}{badge}</div></div>
        </div>""",
        unsafe_allow_html=True,
    )


def build_chart(p: Processor) -> go.Figure:
    fig = go.Figure()
    fig.add_hrect(y0=config.LOWER, y1=config.UPPER, fillcolor=COLORS["band"], line_width=0, layer="below")
    fig.add_trace(go.Scatter(
        x=p.positions, y=p.weights, mode="lines", name="도금량",
        line=dict(color=COLORS["series"], width=2),
        hovertemplate=f"위치 %{{x}} m<br>도금량 %{{y:.{config.DECIMALS}f}} {config.UNIT}<extra></extra>",
    ))
    # 기준을 벗어난 점은 상태별 색으로 강조 (FR-2.4)
    for status in ("HIGH", "LOW"):
        idx = [i for i, s in enumerate(p.statuses) if s == status]
        if idx:
            fig.add_trace(go.Scatter(
                x=[p.positions[i] for i in idx], y=[p.weights[i] for i in idx], mode="markers",
                name=STATUS_LABELS[status], hoverinfo="skip",
                marker=dict(color=COLORS[status], size=8, line=dict(color=COLORS["surface"], width=1.5)),
            ))
    for value, label, color, text_color in (
        (config.UPPER, f"상한 {config.UPPER}", COLORS["HIGH"], "#ffffff"),
        (config.TARGET, f"목표/하한 {config.TARGET}", COLORS["LOW"], "#0b0b0b"),
    ):
        fig.add_hline(y=value, line=dict(color=color, width=2, dash="dash"))
        fig.add_annotation(x=1, xref="paper", xanchor="right", y=value, yref="y", text=f"<b>{label}</b>",
                           showarrow=False, bgcolor=color, font=dict(color=text_color, size=13), borderpad=4)
    x_max = max(p.positions[-1] if p.positions else 0, 50)
    axis = dict(gridcolor=COLORS["grid"], linecolor=COLORS["axis"], zeroline=False,
                tickfont=dict(size=13, color=COLORS["muted"]))
    fig.update_layout(
        height=560, margin=dict(l=60, r=20, t=20, b=50), showlegend=False,
        paper_bgcolor=COLORS["surface"], plot_bgcolor=COLORS["surface"],
        font=dict(family="Pretendard, Malgun Gothic, sans-serif", color=COLORS["text2"]),
        xaxis=dict(axis, title=dict(text="위치 [m]", font=dict(size=14)), range=[0, x_max * 1.02]),
        yaxis=dict(axis, title=dict(text=f"도금량 [{config.UNIT}]", font=dict(size=14)),
                   range=[config.VALUE_MIN, config.VALUE_MAX], dtick=5),
        hoverlabel=dict(bgcolor=COLORS["surface"], font_size=14),
        uirevision=p.coil_no,  # 같은 코일 동안은 확대·이동 상태 유지
    )
    return fig


def render_alert(alert: Alert) -> None:
    title, message = ALERT_TEXT[alert.type]
    icon = STATUS_ICONS[alert.type]
    st.markdown('<div class="alert-backdrop"></div>', unsafe_allow_html=True)
    with st.container(key=f"alert_{alert.type.lower()}"):
        st.markdown(
            f"""<div class="alert-head" role="alertdialog">{icon} {title}</div>
            <p class="alert-msg">{message}</p>
            <div class="alert-value"><small>측정 도금량</small>
              <strong class="num">{fmt(alert.weight)}</strong><span class="unit">{config.UNIT}</span></div>
            <div class="alert-details">
              <span>코일번호</span><span>{alert.coil_no}</span>
              <span>강종</span><span>{alert.steel_grade}</span>
              <span>위치</span><span class="num">{alert.position} m</span>
              <span>발생시각</span><span class="num">{alert.occurred_at:%Y-%m-%d %H:%M:%S}</span>
            </div>""",
            unsafe_allow_html=True,
        )
        # 버튼 키는 'alert_'로 시작하지 않게 한다 (경고창 컨테이너용 .st-key-alert_* 스타일이 버튼에 붙지 않도록)
        st.button("확인", key="confirm_alert", on_click=on_confirm_alert, width="stretch")


def live_view(records: list[dict]) -> None:
    """재생 중에는 주기적으로 다시 실행되는 영역 (카드·그래프·상태바·경고창)."""
    ss = st.session_state
    was_playing = ss.state == "playing"
    advance(records)
    p: Processor = ss.processor

    render_cards(p)
    st.plotly_chart(build_chart(p), key="chart", theme=None, config={"displaylogo": False})

    coil, coil_total = progress(records)
    st.markdown(
        f"""<div class="statusbar">
          <span>재생 진행<b class="num">코일 {coil} / {coil_total} · 레코드 {ss.index:,} / {len(records):,}</b></span>
          <span><span class="dot {ss.state}"></span><b>{PLAYBACK_LABELS[ss.state]}</b></span>
        </div>""",
        unsafe_allow_html=True,
    )
    if ss.alert:
        render_alert(ss.alert)
    if was_playing and ss.state == "ended":
        st.rerun()  # 버튼 상태와 자동 갱신을 멈추기 위해 전체 화면을 다시 그린다


def main() -> None:
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    ss = st.session_state

    try:
        records = load_records()
    except (OSError, json.JSONDecodeError) as err:
        records = []
        ss.state = "error"
        st.error(f"더미 데이터를 불러오지 못했습니다: {err}")

    title_col, *button_cols, speed_col = st.columns([5, 1, 1, 1, 1], vertical_alignment="center")
    title_col.markdown('<h1 class="app-title">도금량 실시간 모니터링</h1>', unsafe_allow_html=True)
    state = ss.state
    button_cols[0].button("▶ 시작", type="primary", width="stretch", on_click=on_start,
                          disabled=state not in ("idle", "paused"))
    button_cols[1].button("❚❚ 일시정지", width="stretch", on_click=on_pause, disabled=state != "playing")
    button_cols[2].button("↺ 처음부터", width="stretch", on_click=on_restart, disabled=state in ("idle", "error"))
    speed_col.selectbox("속도", config.SPEEDS, index=config.SPEEDS.index(ss.speed), key="speed_select",
                        format_func=lambda s: f"×{s} ({config.METERS_PER_SECOND * s} m/s)",
                        on_change=on_speed_change, label_visibility="collapsed", disabled=state == "error")

    run_every = config.REFRESH_SECONDS if ss.state == "playing" else None
    st.fragment(live_view, run_every=run_every)(records)


main()
