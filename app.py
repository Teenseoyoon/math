import streamlit as st
import json
import random
import time
from pathlib import Path

# -------------------------------
# App constants
# -------------------------------
QUIZ_SECONDS = 5 * 60  # 5분
SUBJECTS = ["수(상)", "수(하)", "수1", "수2"]
DATA_PATH = Path("data/questions.json")

# -------------------------------
# Sample fallback questions
# -------------------------------
SAMPLE_QUESTIONS = {
    "수(상)": [
        {"question": "함수 f(x)=x^2-4x+5의 최소값은?",
         "choices": ["0", "1", "2", "3"],
         "answer": 1,
         "explanation": "완전제곱식 (x-2)^2+1 ⇒ 최소값 1"}
    ],
    "수(하)": [
        {"question": "등차수열 3,7,11,... 의 10번째 항은?",
         "choices": ["37", "39", "41", "43"],
         "answer": 1,
         "explanation": "a_n=3+(n-1)*4 ⇒ a_10=39"}
    ],
    "수1": [
        {"question": "함수 y=sin x의 최대값은?",
         "choices": ["-1", "0", "1", "2"],
         "answer": 2,
         "explanation": "sin x의 최댓값은 1"}
    ],
    "수2": [
        {"question": "지수함수 y=2^x에서 y=16일 때 x는?",
         "choices": ["2", "3", "4", "5"],
         "answer": 2,
         "explanation": "2^x=16=2^4 ⇒ x=4"}
    ]
}

# -------------------------------
# Utils
# -------------------------------
def load_questions() -> dict:
    try:
        if DATA_PATH.exists():
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for subj in SUBJECTS:
                data.setdefault(subj, [])
            return data
    except Exception:
        pass
    return SAMPLE_QUESTIONS

def init_state():
    defaults = {
        "page": "home",
        "subject": None,
        "questions": load_questions(),
        "current_q_index": None,
        "start_time": None,
        "answered": False,
        "is_correct": None,
        "timer_expired": False,
        "last_q_index": {s: None for s in SUBJECTS},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def pick_new_question(subject: str):
    q_list = st.session_state["questions"].get(subject, [])
    if not q_list:
        st.session_state["current_q_index"] = None
        return
    candidates = list(range(len(q_list)))
    last = st.session_state["last_q_index"].get(subject)
    if last is not None and len(candidates) > 1 and last in candidates:
        candidates.remove(last)
    idx = random.choice(candidates)
    st.session_state["current_q_index"] = idx
    st.session_state["last_q_index"][subject] = idx

def start_timer():
    st.session_state["start_time"] = time.time()
    st.session_state["timer_expired"] = False
    st.session_state["answered"] = False
    st.session_state["is_correct"] = None

def remaining_seconds() -> int:
    if st.session_state["start_time"] is None:
        return QUIZ_SECONDS
    elapsed = int(time.time() - st.session_state["start_time"])
    remain = max(0, QUIZ_SECONDS - elapsed)
    if remain == 0 and not st.session_state["timer_expired"]:
        st.session_state["timer_expired"] = True
    return remain

def fmt_mmss(sec: int) -> str:
    m, s = divmod(sec, 60)
    return f"{m:02d}:{s:02d}"

# -------------------------------
# Pages
# -------------------------------
def page_home():
    st.title("수학 문제 앱 (Streamlit)")
    st.write("1) **시작** → 2) 교과 선택 → 3) 문제 풀이(5분 타이머)")
    if st.button("시작", type="primary"):
        st.session_state["page"] = "select"
        st.experimental_rerun()

def page_select_subject():
    st.title("교과 선택")
    subject = st.radio("교과", SUBJECTS, index=0, horizontal=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("문제 시작", type="primary"):
            st.session_state["subject"] = subject
            pick_new_question(subject)
            start_timer()
            st.session_state["page"] = "quiz"
            st.experimental_rerun()
    with c2:
        if st.button("← 처음으로"):
            st.session_state["page"] = "home"
            st.experimental_rerun()

def page_quiz():
    st.title("문제 풀이")
    subject = st.session_state.get("subject")
    q_idx = st.session_state.get("current_q_index")
    q_list = st.session_state["questions"].get(subject, [])

    top = st.container()
    with top:
        l, r = st.columns([3, 1])
        with l:
            st.markdown(f"**교과:** {subject}")
        with r:
            remain = remaining_seconds()
            st.metric("남은 시간", fmt_mmss(remain))
            # 선택 라이브러리(없어도 동작): 자동 1초 새로고침
            try:
                from streamlit_autorefresh import st_autorefresh
                st_autorefresh(interval=1000, key="_timer_autorefresh")
            except Exception:
                st.caption("⏱ 자동 새로고침을 쓰려면 requirements.txt에 streamlit-autorefresh를 추가하세요.")

    if q_idx is None or not q_list:
        st.warning("해당 교과 문제 없음. data/questions.json을 추가해 보세요.")
        if st.button("교과 다시 선택"):
            st.session_state["page"] = "select"
            st.experimental_rerun()
        return

    q = q_list[q_idx]
    st.subheader("문제")
    st.write(q["question"])

    disabled = st.session_state["answered"] or st.session_state["timer_expired"]
    if st.session_state["timer_expired"]:
        st.error("⏰ 시간 종료! 다음 문제로 넘어가세요.")

    st.divider()
    st.subheader("선지")

    cols = st.columns(2)
    pressed_idx = None
    for i, choice in enumerate(q["choices"]):
        with cols[i % 2]:
            if st.button(choice, key=f"choice_btn_{i}", disabled=disabled):
                pressed_idx = i

    if pressed_idx is not None and not disabled:
        st.session_state["answered"] = True
        is_correct = (pressed_idx == q["answer"])
        st.session_state["is_correct"] = is_correct
        if is_correct:
            st.success("정답입니다! ✅")
        else:
            st.error("오답입니다. ❌")
        with st.expander("해설 보기"):
            st.write(q.get("explanation", "해설이 없습니다."))

    st.divider()
    a, b, c = st.columns(3)
    with a:
        if st.button("← 교과 선택으로"):
            st.session_state["page"] = "select"
            st.experimental_rerun()
    with b:
        if st.button("현재 문제 다시 풀기"):
            start_timer()
            st.session_state["answered"] = False
            st.session_state["is_correct"] = None
            st.experimental_rerun()
    with c:
        if st.button("다음 문제 →", type="primary"):
            pick_new_question(subject)
            start_timer()
            st.experimental_rerun()

# -------------------------------
# Main
# -------------------------------
init_state()
page = st.session_state["page"]
if page == "home":
    page_home()
elif page == "select":
    page_select_subject()
else:
    page_quiz()
