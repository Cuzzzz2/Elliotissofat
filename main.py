import base64
import io
import math
import struct
import wave

import streamlit as st

# ------------------------------------------------------------
# 거지 탈출 RPG - Streamlit Clicker
# Inspired by the clicker/idle-game genre.
# ------------------------------------------------------------

st.set_page_config(
    page_title="거지 탈출 RPG",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Stage data ----------
STAGES = [
    {
        "name": "1스테이지 · 시골 탈출",
        "short": "시골",
        "goal": 1_000_000,
        "emoji": "🌾",
        "description": "시골에서 시작해 첫 번째 탈출 자금을 모아보자!",
        "bg": "linear-gradient(135deg, #8bc34a 0%, #dcedc8 55%, #fff8e1 100%)",
    },
    {
        "name": "2스테이지 · 길거리 탈출",
        "short": "길거리",
        "goal": 5_000_000,
        "emoji": "🚶",
        "description": "인도에서 버티며 더 큰 탈출 자금을 모아보자!",
        "bg": "linear-gradient(135deg, #90a4ae 0%, #eceff1 50%, #fffde7 100%)",
    },
    {
        "name": "3스테이지 · 반지하 탈출",
        "short": "반지하",
        "goal": 50_000_000,
        "emoji": "🏠",
        "description": "반지하를 탈출하고 한 단계 더 올라가자!",
        "bg": "linear-gradient(135deg, #455a64 0%, #78909c 45%, #cfd8dc 100%)",
    },
    {
        "name": "4스테이지 · 1층 탈출",
        "short": "1층집",
        "goal": 250_000_000,
        "emoji": "🏡",
        "description": "이제 1층집이다. 더 높은 곳을 향해 가자!",
        "bg": "linear-gradient(135deg, #ffcc80 0%, #ffe0b2 45%, #f5f5f5 100%)",
    },
    {
        "name": "5스테이지 · 지방도시 탈출",
        "short": "지방도시 아파트",
        "goal": 1_250_000_000,
        "emoji": "🏙️",
        "description": "지방도시 아파트까지 올라왔다. 마지막 탈출을 완성하자!",
        "bg": "linear-gradient(135deg, #7986cb 0%, #c5cae9 50%, #e8eaf6 100%)",
    },
]

# ---------- Helpers ----------
def won_stage(stage_index: int, money: int) -> bool:
    return money >= STAGES[stage_index]["goal"]


def format_money(value: int) -> str:
    return f"{value:,}원"


def format_compact(value: int) -> str:
    if value >= 100_000_000:
        return f"{value / 100_000_000:.2f}억"
    if value >= 10_000:
        return f"{value / 10_000:.1f}만"
    return f"{value:,}"


def make_beep_wav_base64():
    """Create a tiny beep in memory so no external audio file is required."""
    sample_rate = 22050
    duration = 0.08
    frequency = 880
    amplitude = 4500
    frames = int(sample_rate * duration)

    raw = bytearray()
    for i in range(frames):
        envelope = 1 - (i / frames)
        sample = int(
            amplitude
            * envelope
            * math.sin(2 * math.pi * frequency * i / sample_rate)
        )
        raw.extend(struct.pack("<h", sample))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw)

    return base64.b64encode(buf.getvalue()).decode("ascii")


def play_click_sound():
    audio = make_beep_wav_base64()
    st.markdown(
        f"""
        <audio autoplay>
            <source src="data:audio/wav;base64,{audio}" type="audio/wav">
        </audio>
        """,
        unsafe_allow_html=True,
    )


# ---------- Initial state ----------
if "money" not in st.session_state:
    st.session_state.money = 0

if "stage" not in st.session_state:
    st.session_state.stage = 0

if "income_per_click" not in st.session_state:
    st.session_state.income_per_click = 1_000

if "extra_clicks" not in st.session_state:
    st.session_state.extra_clicks = 0

if "income_upgrade_level" not in st.session_state:
    st.session_state.income_upgrade_level = 0

if "extra_click_upgrade_level" not in st.session_state:
    st.session_state.extra_click_upgrade_level = 0

if "click_count" not in st.session_state:
    st.session_state.click_count = 0

if "last_gain" not in st.session_state:
    st.session_state.last_gain = 0

if "stage_message" not in st.session_state:
    st.session_state.stage_message = ""


def reset_game():
    st.session_state.money = 0
    st.session_state.stage = 0
    st.session_state.income_per_click = 1_000
    st.session_state.extra_clicks = 0
    st.session_state.income_upgrade_level = 0
    st.session_state.extra_click_upgrade_level = 0
    st.session_state.click_count = 0
    st.session_state.last_gain = 0
    st.session_state.stage_message = ""


def check_stage_progress():
    current = st.session_state.stage

    while current < len(STAGES) - 1 and won_stage(current, st.session_state.money):
        current += 1
        st.session_state.stage = current
        st.session_state.stage_message = (
            f"🎉 {STAGES[current]['name']}에 도착했습니다!"
        )

    # Final clear
    if current == len(STAGES) - 1 and st.session_state.money >= STAGES[-1]["goal"]:
        st.session_state.stage_message = (
            "🏆 모든 스테이지를 탈출했습니다! 최종 클리어!"
        )


def buy_income_upgrade():
    level = st.session_state.income_upgrade_level
    cost = int(1_000 * (1.5 ** level))

    if st.session_state.money >= cost:
        st.session_state.money -= cost
        st.session_state.income_upgrade_level += 1
        st.session_state.income_per_click += 1_000
        st.session_state.stage_message = "🛒 클릭 수입 업그레이드 완료!"


def buy_extra_click_upgrade():
    level = st.session_state.extra_click_upgrade_level
    cost = int(1_000 * (1.5 ** level))

    if st.session_state.money >= cost:
        st.session_state.money -= cost
        st.session_state.extra_click_upgrade_level += 1
        st.session_state.extra_clicks += 1
        st.session_state.stage_message = "🛒 추가 클릭 업그레이드 완료!"


# ---------- CSS ----------
current_stage = STAGES[st.session_state.stage]
st.markdown(
    f"""
    <style>
    .stApp {{
        background: {current_stage["bg"]};
    }}

    .main-title {{
        text-align: center;
        font-size: 3rem;
        font-weight: 900;
        margin: 0.2rem 0 0;
        color: #263238;
        text-shadow: 1px 2px 0 rgba(255,255,255,0.7);
    }}

    .subtitle {{
        text-align: center;
        color: #455a64;
        margin-bottom: 1.2rem;
        font-size: 1.05rem;
    }}

    .money-card {{
        background: rgba(255,255,255,0.88);
        border: 2px solid rgba(0,0,0,0.08);
        border-radius: 22px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.10);
    }}

    .money-label {{
        font-size: 0.95rem;
        color: #546e7a;
        font-weight: 700;
    }}

    .money-value {{
        font-size: 2.3rem;
        font-weight: 900;
        color: #1b5e20;
        margin-top: 2px;
    }}

    .stage-badge {{
        display: inline-block;
        padding: 7px 14px;
        border-radius: 999px;
        background: rgba(255,255,255,0.82);
        font-weight: 800;
        color: #37474f;
        border: 1px solid rgba(0,0,0,0.08);
    }}

    .click-effect {{
        position: fixed;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        z-index: 9999;
        pointer-events: none;
        font-size: 2.2rem;
        font-weight: 1000;
        color: #2e7d32;
        text-shadow: 0 2px 5px rgba(255,255,255,0.9);
        animation: floatFade 0.85s ease-out forwards;
    }}

    @keyframes floatFade {{
        0% {{
            opacity: 1;
            transform: translate(-50%, -20%);
        }}
        100% {{
            opacity: 0;
            transform: translate(-50%, -150%);
        }}
    }}

    .character {{
        text-align: center;
        font-size: 7rem;
        line-height: 1;
        padding: 1.2rem 0 0.5rem;
        filter: drop-shadow(0 8px 5px rgba(0,0,0,0.12));
    }}

    .scene {{
        background: rgba(255,255,255,0.45);
        border-radius: 28px;
        border: 2px solid rgba(255,255,255,0.75);
        padding: 12px 20px 20px;
        text-align: center;
        min-height: 255px;
        box-shadow: inset 0 0 30px rgba(255,255,255,0.25);
    }}

    .scene-title {{
        font-size: 1.25rem;
        font-weight: 900;
        color: #263238;
    }}

    .scene-description {{
        color: #455a64;
        margin-bottom: 0;
    }}

    .progress-label {{
        display: flex;
        justify-content: space-between;
        font-weight: 800;
        color: #37474f;
        margin-bottom: 5px;
    }}

    .notice {{
        background: rgba(255,255,255,0.86);
        border-radius: 15px;
        padding: 12px 16px;
        margin: 8px 0;
        text-align: center;
        font-weight: 800;
        color: #37474f;
        border: 1px solid rgba(0,0,0,0.06);
    }}

    div[data-testid="stButton"] > button {{
        border-radius: 16px;
        font-weight: 900;
    }}

    .big-click button {{
        min-height: 110px !important;
        font-size: 1.65rem !important;
    }}

    section[data-testid="stSidebar"] {{
        background: rgba(255,255,255,0.88);
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown('<div class="main-title">💰 거지 탈출 RPG</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">클릭하고 · 업그레이드하고 · 5개의 스테이지를 탈출하자!</div>',
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("🛒 상점")

    income_cost = int(1_000 * (1.5 ** st.session_state.income_upgrade_level))
    extra_cost = int(1_000 * (1.5 ** st.session_state.extra_click_upgrade_level))

    st.markdown("### 💵 +1000원 상승")
    st.caption(
        f"현재 클릭당 {format_money(st.session_state.income_per_click)}"
    )
    st.caption(f"업그레이드 비용: {format_money(income_cost)}")

    if st.button(
        "구매하기",
        key="buy_income",
        use_container_width=True,
        disabled=st.session_state.money < income_cost,
    ):
        buy_income_upgrade()
        st.rerun()

    st.divider()

    st.markdown("### 👆 추가 클릭")
    st.caption(
        f"현재 1회 클릭 = {1 + st.session_state.extra_clicks}회 클릭 취급"
    )
    st.caption(f"업그레이드 비용: {format_money(extra_cost)}")

    if st.button(
        "구매하기",
        key="buy_extra",
        use_container_width=True,
        disabled=st.session_state.money < extra_cost,
    ):
        buy_extra_click_upgrade()
        st.rerun()

    st.divider()

    st.markdown("### 📊 능력치")
    st.metric("클릭당 수입", format_money(st.session_state.income_per_click))
    st.metric("1회 클릭 취급", f"{1 + st.session_state.extra_clicks}회")
    st.metric("총 클릭 횟수", f"{st.session_state.click_count:,}")

    st.divider()

    if st.button("🔄 게임 초기화", use_container_width=True):
        reset_game()
        st.rerun()

# ---------- Progress ----------
stage_index = st.session_state.stage
stage = STAGES[stage_index]
goal = stage["goal"]

st.markdown(
    f'<div style="text-align:center"><span class="stage-badge">'
    f'{stage["emoji"]} {stage["name"]}</span></div>',
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        f"""
        <div class="money-card">
            <div class="money-label">현재 보유 금액</div>
            <div class="money-value">{format_money(st.session_state.money)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="money-card">
            <div class="money-label">클릭 1회 수입</div>
            <div class="money-value">{format_money(st.session_state.income_per_click)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class="money-card">
            <div class="money-label">스테이지 목표</div>
            <div class="money-value">{format_money(goal)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

progress = min(st.session_state.money / goal, 1.0)
st.markdown(
    f"""
    <div class="progress-label">
        <span>탈출 진행도</span>
        <span>{progress * 100:.1f}%</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.progress(progress)

if stage_index < len(STAGES) - 1:
    remaining = max(goal - st.session_state.money, 0)
    st.caption(f"다음 스테이지까지 {format_money(remaining)} 필요")
else:
    remaining = max(goal - st.session_state.money, 0)
    if remaining > 0:
        st.caption(f"최종 클리어까지 {format_money(remaining)} 필요")

if st.session_state.stage_message:
    st.markdown(
        f'<div class="notice">{st.session_state.stage_message}</div>',
        unsafe_allow_html=True,
    )

# ---------- Main scene ----------
left, center, right = st.columns([1, 2, 1])

with center:
    st.markdown('<div class="scene">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="character">{stage["emoji"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="scene-title">{stage["short"]} 생활</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="scene-description">{stage["description"]}</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="big-click">', unsafe_allow_html=True)
    if st.button(
        "💸 돈 벌기!\n+"
        + format_money(
            st.session_state.income_per_click * (1 + st.session_state.extra_clicks)
        ),
        key="earn_button",
        use_container_width=True,
    ):
        effective_clicks = 1 + st.session_state.extra_clicks
        gain = st.session_state.income_per_click * effective_clicks
        st.session_state.money += gain
        st.session_state.click_count += effective_clicks
        st.session_state.last_gain = gain
        play_click_sound()
        check_stage_progress()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Render the fade-out number after the button interaction.
# Streamlit reruns, so this appears for the latest click.
if st.session_state.last_gain > 0:
    st.markdown(
        f'<div class="click-effect">+{format_money(st.session_state.last_gain)}</div>',
        unsafe_allow_html=True,
    )

# ---------- Stage roadmap ----------
st.write("")
st.subheader("🗺️ 탈출 로드맵")

road_cols = st.columns(len(STAGES))
for i, stage_info in enumerate(STAGES):
    with road_cols[i]:
        if i < st.session_state.stage:
            status = "✅ 탈출"
        elif i == st.session_state.stage:
            status = "🔥 진행 중"
        else:
            status = "🔒 잠김"

        st.markdown(
            f"""
            <div class="notice">
                <div style="font-size:1.8rem">{stage_info["emoji"]}</div>
                <div>{stage_info["short"]}</div>
                <div style="font-size:0.85rem">{format_money(stage_info["goal"])}</div>
                <div style="margin-top:5px">{status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

if st.session_state.stage == len(STAGES) - 1 and st.session_state.money >= STAGES[-1]["goal"]:
    st.success("🏆 최종 클리어! 5개 스테이지의 탈출에 성공했습니다!")
