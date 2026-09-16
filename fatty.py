import base64
import io
import math
import struct
import wave
import streamlit as st

st.set_page_config(page_title="거지 탈출 RPG", page_icon="💰", layout="wide")

STAGES = [
    ("시골 탈출", "시골", 1_000_000, "🌾"),
    ("길거리 탈출", "인도", 5_000_000, "🚶"),
    ("반지하 탈출", "반지하", 50_000_000, "🏚️"),
    ("1층 탈출", "1층집", 250_000_000, "🏠"),
    ("지방도시 탈출", "지방도시 아파트", 1_250_000_000, "🏢"),
]

for k, v in {
    "money": 0, "stage": 0, "income": 1000, "extra": 0,
    "income_lv": 0, "extra_lv": 0, "clicks": 0, "gain": 0, "fx": 0,
    "message": ""
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

def fmt(n):
    return f"{int(n):,}"

def cost(level):
    return int(1000 * (1.5 ** level))

def beep():
    sr, duration, freq = 22050, .07, 950
    raw = bytearray()
    for i in range(int(sr * duration)):
        env = 1 - i / int(sr * duration)
        x = int(5000 * env * math.sin(2 * math.pi * freq * i / sr))
        raw += struct.pack("<h", x)
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(raw)
    return base64.b64encode(b.getvalue()).decode()

def sound():
    st.markdown(
        f'<audio autoplay><source src="data:audio/wav;base64,{beep()}" type="audio/wav"></audio>',
        unsafe_allow_html=True
    )

def reset():
    for k, v in {"money":0,"stage":0,"income":1000,"extra":0,
                 "income_lv":0,"extra_lv":0,"clicks":0,"gain":0,"fx":0,
                 "message":""}.items():
        st.session_state[k] = v

def progress_stage():
    while st.session_state.stage < 4 and st.session_state.money >= STAGES[st.session_state.stage][2]:
        st.session_state.stage += 1
        st.session_state.message = f"🎉 {STAGES[st.session_state.stage][0]} 도착!"
    if st.session_state.stage == 4 and st.session_state.money >= STAGES[4][2]:
        st.session_state.message = "🏆 모든 스테이지 탈출 성공!"

stage_name, place, goal, emoji = STAGES[st.session_state.stage]
pct = min(st.session_state.money / goal, 1)

# Single-screen game UI. Inspired by the visual language of Korean idle/clicker games,
# but uses original UI/layout and emoji-based scene art.
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&family=Noto+Sans+KR:wght@500;700;900&display=swap');
html,body,.stApp,[data-testid="stAppViewContainer"] {{height:100%; overflow:hidden;}}
.block-container {{max-width:1450px; height:100vh; padding:8px 18px !important; overflow:hidden;}}
* {{font-family:'Noto Sans KR',sans-serif;}}
.stApp {{background:linear-gradient(#f7e5c1,#e4c99b);}}
.title {{font-family:'Jua'!important;text-align:center;color:#4b3020;font-size:32px;line-height:1;margin:0}}
.sub {{text-align:center;color:#795548;font-size:11px;margin-bottom:6px}}
.money {{background:#fff7df;border:3px solid #916237;border-radius:15px;box-shadow:0 4px #654427;padding:4px;text-align:center}}
.money b {{display:block;color:#4e7b20;font-family:'Jua'!important;font-size:25px}}
.money span {{font-size:11px;color:#765337;font-weight:900}}
.scene,.shop {{height:58vh;min-height:390px;border:4px solid #80582f;border-radius:24px;box-shadow:0 7px #5d4027,0 14px 25px #76553344;box-sizing:border-box}}
.scene {{position:relative;overflow:hidden;background:
linear-gradient(180deg,rgba(255,255,255,.18),transparent 50%),
linear-gradient(180deg,
{('#a9d86e 0%,#dceca8 55%,#b58a58 56%,#8c6545 100%' if st.session_state.stage==0 else
'#a6d9f2 0%,#d9edf3 55%,#8f8f8c 56%,#666662 100%' if st.session_state.stage==1 else
'#3b444b 0%,#646d73 55%,#5a4335 56%,#32271f 100%' if st.session_state.stage==2 else
'#bfe1ef 0%,#edf6f8 55%,#c6a477 56%,#97724d 100%' if st.session_state.stage==3 else
'#86bce2 0%,#dceef8 55%,#777d87 56%,#454a53 100%')});}}
.scene .label {{position:absolute;top:12px;left:14px;background:#fff4d4eF;border:2px solid #8d6036;border-radius:11px;padding:4px 10px;font-family:'Jua'!important;color:#513622;z-index:3}}
.sun {{position:absolute;right:7%;top:7%;font-size:48px}}
.person {{position:absolute;left:50%;top:47%;transform:translate(-50%,-50%);font-size:125px;filter:drop-shadow(0 10px 5px #34200a55)}}
.caption {{position:absolute;left:50%;top:70%;transform:translateX(-50%);white-space:nowrap;background:#fff7e5eF;border:2px solid #8d6036;border-radius:12px;padding:5px 12px;color:#513622;font-size:12px;font-weight:900}}
.ground {{position:absolute;bottom:10%;left:0;right:0;text-align:center;font-size:48px;letter-spacing:15px;opacity:.8}}
.barwrap {{position:absolute;left:7%;right:7%;bottom:3%;z-index:3}}
.bartext {{display:flex;justify-content:space-between;color:white;text-shadow:0 2px 3px #432;font-size:11px;font-weight:900}}
.bar {{height:15px;background:#44382dcc;border:2px solid #fff0c9;border-radius:99px;overflow:hidden}}
.fill {{height:100%;width:{pct*100}%;background:linear-gradient(90deg,#74b936,#d8ee58)}}
.shop {{background:linear-gradient(#fff1c9,#e5bf80);padding:10px}}
.shop h2 {{font-family:'Jua'!important;text-align:center;color:#563a25;font-size:23px;margin:0}}
.card {{background:linear-gradient(145deg,#fffdf2,#efd39e);border:2px solid #9a6a39;border-radius:15px;padding:8px;margin:7px 0;box-shadow:0 4px #76502d55}}
.card strong {{font-family:'Jua'!important;color:#513522;font-size:17px}}
.card small {{display:block;color:#6b4b32;font-size:10px;line-height:1.45}}
.cost {{color:#ad501c;font-weight:900}}
.stats {{background:#fff9e8bb;border:2px solid #aa7944;border-radius:12px;padding:7px;color:#563b27;font-size:10px;line-height:1.55}}
div[data-testid="stButton"]>button {{background:linear-gradient(#ffe991,#eebc43)!important;border:2px solid #80562f!important;color:#4d321f!important;border-radius:13px!important;font-weight:900!important;box-shadow:0 4px #80562f!important}}
.earn button {{min-height:70px!important;font-size:21px!important}}
.float {{position:fixed;left:50%;top:45%;z-index:9999;pointer-events:none;color:#2e8b28;font-family:'Jua'!important;font-size:40px;font-weight:900;text-shadow:0 2px white,2px 0 white,-2px 0 white;animation:fade .85s ease-out forwards}}
@keyframes fade {{0%{{opacity:0;transform:translate(-50%,-20%) scale(.7)}}15%{{opacity:1;transform:translate(-50%,-50%) scale(1.1)}}100%{{opacity:0;transform:translate(-50%,-145%) scale(.9)}}}}
@media(max-width:900px){{html,body,.stApp,[data-testid="stAppViewContainer"]{{overflow:auto}}.block-container{{height:auto;overflow:visible}}.scene,.shop{{height:480px}}}}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">💰 거지 탈출 RPG</div><div class="sub">돈을 모으고 더 나은 곳으로 탈출하자!</div>', unsafe_allow_html=True)

a,b,c=st.columns([1,1.4,1])
with a: st.markdown(f'<div class="money"><span>현재 보유 금액</span><b>₩ {fmt(st.session_state.money)}</b></div>',unsafe_allow_html=True)
with b: st.markdown(f'<div class="money"><span>현재 스테이지</span><b style="font-size:22px">{st.session_state.stage+1}/5 · {stage_name}</b></div>',unsafe_allow_html=True)
with c: st.markdown(f'<div class="money"><span>탈출 목표</span><b style="font-size:22px">₩ {fmt(goal)}</b></div>',unsafe_allow_html=True)

st.write("")
left,right=st.columns([2.25,1],gap="medium")

with left:
    ground = ["🌱 🌾 🌱 🌾 🌱","🚧 🧱 🚶 🧱 🚧","🪟 🧱 🪟 🧱 🪟","🌳 🪟 🚪 🪟 🌳","🌳 🏢 🏢 🏢 🌳"][st.session_state.stage]
    st.markdown(f"""
    <div class="scene">
      <div class="label">{emoji} {st.session_state.stage+1}스테이지 · {stage_name}</div>
      <div class="sun">☀️</div>
      <div class="ground">{ground}</div>
      <div class="person">{emoji}🧍</div>
      <div class="caption">{place}에서 탈출 자금을 모으는 중...</div>
      <div class="barwrap">
        <div class="bartext"><span>탈출 진행도</span><span>{pct*100:.1f}%</span></div>
        <div class="bar"><div class="fill"></div></div>
      </div>
    </div>
    """,unsafe_allow_html=True)
    st.markdown('<div class="earn">',unsafe_allow_html=True)
    gain = st.session_state.income*(1+st.session_state.extra)
    if st.button(f"💸 돈 벌기!   +₩ {fmt(gain)}",use_container_width=True,key="earn"):
        st.session_state.money += gain
        st.session_state.clicks += 1+st.session_state.extra
        st.session_state.gain = gain
        st.session_state.fx += 1
        progress_stage()
        sound()
        st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)

with right:
    icost=cost(st.session_state.income_lv); ecost=cost(st.session_state.extra_lv)
    st.markdown('<div class="shop"><h2>🛒 능력치 상점</h2><div style="text-align:center;color:#805d3e;font-size:10px">업그레이드마다 가격 × 1.5</div>',unsafe_allow_html=True)

    st.markdown(f'<div class="card"><strong>💵 +1000원 상승</strong><small>클릭 1회 수입 +1,000원<br>현재 클릭 수입: <b>₩ {fmt(st.session_state.income)}</b><br>가격: <span class="cost">₩ {fmt(icost)}</span></small></div>',unsafe_allow_html=True)
    if st.button(f"💵 구매 · ₩ {fmt(icost)}",use_container_width=True,disabled=st.session_state.money<icost,key="income_buy"):
        st.session_state.money-=icost; st.session_state.income+=1000; st.session_state.income_lv+=1
        st.session_state.message="💵 클릭 수입 업그레이드!"
        st.rerun()

    st.markdown(f'<div class="card"><strong>👆 추가 클릭</strong><small>1회 클릭을 {1+st.session_state.extra}회 클릭으로 취급<br>현재 추가 클릭: +{st.session_state.extra}<br>가격: <span class="cost">₩ {fmt(ecost)}</span></small></div>',unsafe_allow_html=True)
    if st.button(f"👆 구매 · ₩ {fmt(ecost)}",use_container_width=True,disabled=st.session_state.money<ecost,key="extra_buy"):
        st.session_state.money-=ecost; st.session_state.extra+=1; st.session_state.extra_lv+=1
        st.session_state.message="👆 추가 클릭 업그레이드!"
        st.rerun()

    st.markdown(f'<div class="stats"><b>📊 능력치</b><br>💰 클릭당 기본 수입: ₩ {fmt(st.session_state.income)}<br>👆 1회 클릭 취급: {1+st.session_state.extra}회<br>🖱️ 누적 클릭: {fmt(st.session_state.clicks)}회</div>',unsafe_allow_html=True)
    if st.session_state.message:
        st.markdown(f'<div style="background:#fff4c9;border:2px solid #9a6a39;border-radius:10px;padding:5px;margin-top:7px;text-align:center;font-size:11px;font-weight:900;color:#5c3e27">{st.session_state.message}</div>',unsafe_allow_html=True)
    if st.button("🔄 처음부터 다시 하기",use_container_width=True,key="reset"):
        reset(); st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)

if st.session_state.gain:
    st.markdown(f'<div class="float" key="{st.session_state.fx}">+₩ {fmt(st.session_state.gain)}</div>',unsafe_allow_html=True)
    st.session_state.gain=0
