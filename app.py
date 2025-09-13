# app.py
import json
import os
from pathlib import Path
import streamlit as st

DATA_DIR = Path("data")
JSON_PATH = DATA_DIR / "questions.json"

st.set_page_config(page_title="수학 문제 풀이", page_icon="🧮", layout="centered")

# ---------------------------
# Utilities
# ---------------------------
@st.cache_data(show_spinner=False)
def load_questions():
    if not JSON_PATH.exists():
        return {}
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 보정: 비어 있는 과목은 빈 리스트라도 유지
    for k, v in list(data.items()):
        if v is None:
            data[k] = []
    return data

def get_subject_list(qbank: dict):
    # 문제 있는 과목만 우선 노출 (완전 빈 과목도 선택하려면 아래 주석 해제)
    subjects = [k for k, v in qbank.items() if isinstance(v, list) and len(v) > 0]
    if not subjects:  # 전부 비어있다면 키 전부 노출
        subjects = list(qbank.keys())
    return subjects

def ensure_session_keys():
    if "qbank" not in st.session_state:
        st.session_state.qbank = load_questions()

    if "subject" not in st.session_state:
        subs = get_subject_list(st.session_state.qbank)
        st.session_state.subject = subs[0] if subs else None

    if "qidx" not in st.session_state:
        st.session_state.qidx = 0

    if "responses" not in st.session_state:
        # responses = { subject: { qidx: {"choice": int, "is_correct": bool} } }
        st.session_state.responses = {}

def get_current_question():
    subject = st.session_state.subject
    qidx = st.session_state.qidx
    qlist = st.session_state.qbank.get(subject, [])
    if not qlist:
        return None, 0
    qidx = max(0, min(qidx, len(qlist) - 1))
    st.session_state.qidx = qidx
    return qlist[qidx], len(qlist)

def record_response(subject, qidx, choice_idx, is_correct):
    if subject not in st.session_state.responses:
        st.session_state.responses[subject] = {}
    st.session_state.responses[subject][qidx] = {
        "choice": choice_idx,
        "is_correct": is_correct,
    }

def get_saved_choice(subject, qidx):
    try:
        return st.session_state.responses[subject][qidx]["choice"]
    except Exception:
        return None

# ---------------------------
# Sidebar
# ---------------------------
ensure_session_keys()
qbank = st.session_state.qbank
subjects = get_subject_list(qbank)

with st.sidebar:
    st.header("설정")
    if subjects:
        new_subj = st.selectbox("교과 선택", subjects, index=subjects.index(st.session_state.subject) if st.session_state.subject in subjects else 0)
        if new_subj != st.session_state.subject:
            st.session_state.subject = new_subj
            st.session_state.qidx = 0
    else:
        st.info("questions.json에 과목/문제를 추가해 주세요.")

    # 현재 과목의 전체 문항 수
    current_list = qbank.get(st.session_state.subject, [])
    total_q = len(current_list)
    if total_q > 0:
        new_idx = st.number_input("문항 번호", min_value=1, max_value=total_q, value=st.session_state.qidx + 1, step=1)
        # number_input은 1-based로 보였으면 좋으니 내부는 0-based로 보정
        if (new_idx - 1) != st.session_state.qidx:
            st.session_state.qidx = int(new_idx - 1)

    st.markdown("---")
    st.caption("Tip: 이미지/JSON 경로가 맞지 않으면 아래 본문에 오류가 표시됩니다.")

# ---------------------------
# Main UI
# ---------------------------
st.title("🧮 수학 문제 풀이")

if not subjects or st.session_state.subject is None:
    st.warning("로드할 문제가 없습니다. data/questions.json을 확인해 주세요.")
    st.stop()

question, total_q = get_current_question()
subject = st.session_state.subject
qidx = st.session_state.qidx

if question is None:
    st.info(f"현재 선택된 교과 **{subject}** 에 등록된 문제가 없습니다.")
    st.stop()

# 문제 이미지 & 본문
colL, colR = st.columns([1, 1])
with colL:
    st.subheader(f"{subject} - {qidx+1}번")
    qtext = question.get("question", "").strip()
    if qtext:
        st.markdown(qtext)
with colR:
    img_path = question.get("image", "")
    if not img_path:
        st.error("이미지 경로가 비어 있습니다. questions.json을 확인하세요.")
    else:
        if not Path(img_path).exists():
            st.error(f"이미지 파일을 찾을 수 없습니다.\n`{img_path}`")
        else:
            st.image(img_path, caption=f"{subject} {qidx+1}번", use_container_width=True)

# 선택지
raw_choices = question.get("choices", [])
choices = raw_choices if raw_choices else ["①", "②", "③", "④", "⑤"]

# 저장된 응답(있으면 복원)
saved_choice = get_saved_choice(subject, qidx)
preselect_index = saved_choice if (isinstance(saved_choice, int) and 0 <= saved_choice < len(choices)) else 0

selected = st.radio("정답을 선택하세요", options=list(range(len(choices))), format_func=lambda i: choices[i], index=preselect_index, horizontal=True)

# 정답 확인
correct_index = question.get("answer", None)

btn_cols = st.columns([1, 1, 1, 2])
with btn_cols[0]:
    check = st.button("정답 확인", type="primary")
with btn_cols[1]:
    prev = st.button("이전 문제", disabled=(qidx == 0))
with btn_cols[2]:
    nxt = st.button("다음 문제", disabled=(qidx >= total_q - 1))

# 판정 & 네비게이션
if check:
    if correct_index is None:
        st.error("questions.json에 `answer`가 비어 있습니다.")
    else:
        # ⚠️ 가정: answer는 0-based 인덱스 (예: 2 → '③')
        is_correct = (selected == int(correct_index))
        record_response(subject, qidx, selected, is_correct)
        if is_correct:
            st.success(f"정답입니다! ✅  (선택: {choices[selected]})")
        else:
            try:
                st.error(f"오답입니다. ❌  (선택: {choices[selected]}, 정답: {choices[int(correct_index)]})")
            except Exception:
                st.error("오답입니다. 정답 인덱스가 choices 범위를 벗어납니다. JSON을 확인하세요.")

if prev:
    st.session_state.qidx = max(0, qidx - 1)
    st.rerun()

if nxt:
    st.session_state.qidx = min(total_q - 1, qidx + 1)
    st.rerun()

# 하단: 진행 요약
st.markdown("---")
resp = st.session_state.responses.get(subject, {})
solved = len(resp)
correct_count = sum(1 for v in resp.values() if v.get("is_correct"))
if total_q > 0:
    st.write(f"**진행 상황** — {subject}: {solved}/{total_q} 문항, 정답 {correct_count}개")
