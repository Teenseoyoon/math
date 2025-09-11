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
         "explanation": "2^x=16=2
