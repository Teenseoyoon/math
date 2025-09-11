# Streamlit 수학 문제 앱

## 구조
- app.py : 메인 앱
- requirements.txt : 의존성
- runtime.txt : Python 버전(Cloud용)
- data/questions.json : (선택) 문제은행

## 로컬 실행
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
