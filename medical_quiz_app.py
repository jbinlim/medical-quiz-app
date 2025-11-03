
import streamlit as st
import pandas as pd
import random
import os

# ===== 데이터 불러오기 =====
@st.cache_data
def load_data(path):
    xls = pd.ExcelFile(path, engine='openpyxl')
    sections = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet)
        df = df.dropna(subset=["용어", "뜻"])
        sections[sheet] = list(zip(df["용어"], df["뜻"]))
    return sections

# ===== 파일 경로 설정 (중요) =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
excel_path = os.path.join(BASE_DIR, "medical_terms.xlsx")

# ===== 엑셀 불러오기 =====
try:
    data = load_data(excel_path)
except FileNotFoundError:
    st.error("⚠️ '의학용어정리.xlsx' 파일이 같은 폴더에 필요합니다.")
    st.stop()

# ===== 문제 생성 함수 =====
def make_question(terms):
    eng, kor = random.choice(terms)
    mode = random.choice(["eng_to_kor", "kor_to_eng"])
    if mode == "eng_to_kor":
        question, answer, pool, direction = eng, kor, [t[1] for t in terms], "뜻"
    else:
        question, answer, pool, direction = kor, eng, [t[0] for t in terms], "용어"
    options = [answer]
    while len(options) < 4:
        fake = random.choice(pool)
        if fake not in options:
            options.append(fake)
    random.shuffle(options)
    return question, options, answer, direction


# ===== UI 시작 =====
st.title("💊 의학용어 퀴즈")

sections = list(data.keys()) + ["전체 랜덤"]

# ===== 세션 초기화 =====
if "phase" not in st.session_state:
    st.session_state.phase = "setup"  # setup → question → result
if "checked" not in st.session_state:
    st.session_state.checked = False

# ===== 초기 설정 =====
if st.session_state.phase == "setup":
    section_choice = st.selectbox("단원을 선택하세요:", sections)
    num_q = st.number_input("출제할 문제 수:", 1, 100, 10, 1)
    if st.button("퀴즈 시작"):
        if section_choice == "전체 랜덤":
            st.session_state.terms = [t for sec in data.values() for t in sec]
        else:
            st.session_state.terms = data[section_choice]
        random.shuffle(st.session_state.terms)
        st.session_state.num_q = num_q
        st.session_state.cur_q = 0
        st.session_state.score = 0
        st.session_state.phase = "question"
        st.session_state.checked = False
        st.session_state.q = None
        st.rerun()

# ===== 퀴즈 =====
if st.session_state.phase == "question":
    total = st.session_state.num_q
    idx = st.session_state.cur_q
    terms = st.session_state.terms

    if idx >= total:
        st.session_state.phase = "result"
        st.rerun()

    if st.session_state.q is None:
        q, opts, ans, dir = make_question(terms)
        st.session_state.q, st.session_state.opts = q, opts
        st.session_state.ans, st.session_state.dir = ans, dir

    st.write(f"### 문제 {idx+1} / {total}")
    st.subheader(f"{st.session_state.q} → ({st.session_state.dir})")

    choice = st.radio("정답을 선택하세요:", st.session_state.opts, key=f"choice_{idx}")

    if st.button("정답 확인"):
        st.session_state.checked = True
        if choice == st.session_state.ans:
            st.success("✅ 정답입니다!")
            st.session_state.score += 1
        else:
            st.error(f"❌ 오답입니다. 정답은 [{st.session_state.ans}] 입니다.")
        st.session_state.show_next = True

    if st.session_state.get("checked", False) and st.session_state.get("show_next", False):
        if st.button("➡️ 다음 문제로"):
            st.session_state.checked = False
            st.session_state.show_next = False
            st.session_state.cur_q += 1
            st.session_state.q = None
            st.rerun()

# ===== 결과 =====
if st.session_state.phase == "result":
    st.success("🎉 퀴즈 완료!")
    st.write(f"총 {st.session_state.num_q}문제 중 {st.session_state.score}개 정답 ✅")
    rate = (st.session_state.score / st.session_state.num_q) * 100
    st.write(f"정답률: {rate:.1f}%")

    if st.button("다시 하기"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
