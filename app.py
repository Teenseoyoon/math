import streamlit as st
import json
import random
import time
from pathlib import Path

# -------------------------------
# App constants
# -------------------------------
QUIZ_SECONDS = 5 * 60  # 5 minutes per question
SUBJECTS = ["수(상)", "수(하)", "수1", "수2"]
DATA_PATH = Path("data/questions.json")

# -------------------------------
# Sample fallback questions (used if data/questions.json is missing)
# -------------------------------
SAMPLE_QUESTIONS = {
    "수(상)": [
        {
            "question": "함수 f(x)=x^2-4x+5의 최소값은?",
            "choices": ["0", "1", "2", "3"],
            "answer": 1,
            "explanation": "완전제곱식으로 (x-2)^2+1 이므로 최소값은 1."
        }
    ],
    "수(하)": [
        {
            "question": "등차수열 3, 7, 11, ...의 10번째 항은?",
            "choices": ["37", "39", "41", "43"],
            "answer": 2,
            "explanation": "a_n = 3 + (n-1)*4 → a_10 = 3 + 9*4 = 39이 아니라 39? 다시 계산: 3+36=39. 선택지는 39가 2번이므로 정답은 2."
        }
    ],
    "수1": [
        {
            "question": "함수 y=sin x의 최대값은?",
            "choices": ["-1", "0", "1", "2"],
            "answer": 2,
            "explanation": "삼각함수 기본 범위에서 sin x의 최대값은 1."
        }
    ],
    "수2": [
        {
            "question": "지수함수 y=2^x에서 y가 16일 때 x의 값은?",
            "choices": ["2", "3", "4", "5"],
            "answer": 2,
            "explanation": "2^x=16=2^4 이므로 x=4."
        }
    ]
}

# -------------------------------
# Utility functions
# -------------------------------

def load_questions() -> dict:
    """Load questions from data/questions.json if present, else fallback to SAMPLE_QUESTIONS."""
    try:
        if DATA_PATH.exists():
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # quick validation
            for subj in SUBJECTS:
                if subj not in data:
                    data[subj] = []
            return data
    except Exception:
        pass
    return SAMPLE_QUESTIONS


def init_state():
    default_state = {
        "page": "home",  # home → select → quiz
        "subject": None,
        "questions": load_questions(),
        "current_q_index": None,
        "start_time": None,
        "answered": False,
        "is_correct": None,
        "timer_expired": False,
        "last_q_index": {subj: None for subj in SUBJECTS},
    }
    for k, v in default_state.items():
        if k not in st.session_state:
            st.session_state[k] = v


def pick_new_question(subject: str):
    q_list = st.session_state["questions"].get(subject, [])
    if not q_list:
        st.session_state["current_q_index"] = None
        return
    # avoid immediate repeat if possible
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
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"


# -------------------------------
# UI Pages
# -------------------------------

def page_home():
    st.title("수학 문제 앱 (Streamlit)")
    st.write("1) 시작 화면에서 **시작**을 누르세요 → 2) 교과 선택 → 3) 문제 풀이 (5분 타이머)")
    if st.button("시작", type="primary"):
        st.session_state["page"] = "select"
        st.experimental_rerun()


def page_select_subject():
    st.title("교과 선택")
    st.write("원하는 수학 교과를 선택하세요.")
    subject = st.radio("교과", SUBJECTS, index=0, horizontal=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("문제 시작", type="primary"):
            st.session_state["subject"] = subject
            pick_new_question(subject)
            start_timer()
            st.session_state["page"] = "quiz"
            st.experimental_rerun()
    with col2:
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
        left, right = st.columns([3, 1])
        with left:
            st.markdown(f"**교과:** {subject}")
        with right:
            # Timer display
            remain = remaining_seconds()
            st.metric("남은 시간", fmt_mmss(remain))
            # Optional auto-refresh every second if available
            try:
                from streamlit_autorefresh import st_autorefresh  # optional dependency
                st_autorefresh(interval=1000, key="_timer_autorefresh")
            except Exception:
                # Fallback manual refresh button
                st.caption("⏱ 자동 새로고침을 사용하려면 requirements.txt에 streamlit-autorefresh를 추가하세요.")
                st.button("시간 업데이트", key="_manual_refresh")

    if q_idx is None or not q_list:
        st.warning("해당 교과에 등록된 문제가 없습니다. data/questions.json 파일을 추가해 보세요.")
        if st.button("교과 다시 선택"):
            st.session_state["page"] = "select"
            st.experimental_rerun()
        return

    q = q_list[q_idx]

    st.subheader("문제")
    st.write(q["question"])  # supports plain text; you can switch to st.markdown for formulas

    disabled = st.session_state["answered"] or st.session_state["timer_expired"]
    if st.session_state["timer_expired"]:
        st.error("⏰ 시간 종료! 다음 문제로 넘어가세요.")

    st.divider()
    st.subheader("선지")

    # Choice buttons
    cols = st.columns(2)
    pressed_idx = None
    for i, choice in enumerate(q["choices"]):
        with cols[i % 2]:
            if st.button(choice, key=f"choice_btn_{i}", disabled=disabled):
                pressed_idx = i

    # Evaluate answer
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
    colA, colB, colC = st.columns([1, 1, 1])
    with colA:
        if st.button("← 교과 선택으로"):
            st.session_state["page"] = "select"
            st.experimental_rerun()
    with colB:
        if st.button("현재 문제 다시 풀기"):
            start_timer()
            st.session_state["answered"] = False
            st.session_state["is_correct"] = None
            st.experimental_rerun()
    with colC:
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
