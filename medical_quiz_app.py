import streamlit as st
import pandas as pd
import random
import os
import re

# ==============================
# 📘 데이터 로드
# ==============================
@st.cache_data
def load_data(path):
    """엑셀 파일의 모든 시트를 불러와 dict로 반환"""
    xls = pd.ExcelFile(path, engine="openpyxl")
    data = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet).dropna(subset=["용어", "뜻"])
        data[sheet] = list(zip(df["용어"].astype(str), df["뜻"].astype(str)))
    return data


# ==============================
# 🧠 유틸 함수
# ==============================
def normalize(s: str):
    """비교용 문자열 정규화"""
    return re.sub(r"\s+", "", s.strip().lower())


def make_question(terms, mode):
    """문제 생성"""
    eng, kor = random.choice(terms)
    if mode == "주관식 (직접 입력)":
        return kor, eng, "영문 용어"
    elif random.choice([True, False]):
        return eng, kor, "뜻"
    else:
        return kor, eng, "용어"


def check_answer(choice, correct, mode):
    """정답 여부 판별"""
    if not choice:
        return None
    if mode == "객관식 (4지선다)":
        return choice == correct
    else:
        return normalize(choice) == normalize(correct)


# ==============================
# 🩺 메인 실행
# ==============================
st.title("💊 의학용어 퀴즈")

# ===== 파일 경로 =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
excel_path = os.path.join(BASE_DIR, "medical_terms.xlsx")

# ===== 엑셀 불러오기 =====
try:
    data = load_data(excel_path)
except FileNotFoundError:
    st.error("⚠️ 'medical_terms.xlsx' 파일이 같은 폴더에 필요합니다.")
    st.stop()

# ==============================
# 🎬 세션 상태 초기화
# ==============================
default_state = {
    "phase": "setup",
    "terms": [],
    "cur_idx": 0,
    "score": 0,
    "mode": "",
    "feedback": "",
    "answered": False,
    "wrong_list": [],
}
for k, v in default_state.items():
    st.session_state.setdefault(k, v)


# ==============================
# ⚙️ 퀴즈 설정
# ==============================
if st.session_state.phase == "setup":
    section = st.selectbox("📚 단원 선택:", list(data.keys()) + ["전체 랜덤"])
    mode = st.radio("🎯 출제 모드 선택:", ["객관식 (4지선다)", "주관식 (직접 입력)"])
    scope = st.radio("📏 문제 범위:", ["전체 단원", "직접 개수 지정"])

    num_q = (
        st.number_input("출제할 문제 수:", 1, 200, 10, 1)
        if scope == "직접 개수 지정"
        else None
    )

    if st.button("시작하기 ▶️"):
        terms = [t for sec in data.values() for t in sec] if section == "전체 랜덤" else data[section]
        random.shuffle(terms)
        if num_q:
            terms = terms[:num_q]

        st.session_state.update({
            "phase": "quiz",
            "terms": terms,
            "mode": mode,
            "cur_idx": 0,
            "score": 0,
            "wrong_list": [],
            "feedback": "",
            "answered": False,
        })
        st.rerun()


# ==============================
# 🧩 퀴즈 로직
# ==============================
if st.session_state.phase == "quiz":
    terms = st.session_state.terms
    total = len(terms)
    idx = st.session_state.cur_idx

    if idx >= total:
        st.session_state.phase = "result"
        st.rerun()

    # 새 문제 설정
    if "q_data" not in st.session_state or not st.session_state.answered:
        q, ans, direction = make_question(terms, st.session_state.mode)
        st.session_state.q_data = {"q": q, "ans": ans, "dir": direction}

    q, ans, direction = st.session_state.q_data.values()

    st.markdown(f"### 문제 {idx+1} / {total}")
    st.subheader(f"{q} → ({direction})")

    # 보기 설정
    if st.session_state.mode == "객관식 (4지선다)":
        pool = [a[1] if direction == "뜻" else a[0] for a in terms]
        options = [ans] + random.sample([p for p in pool if p != ans], min(3, len(pool) - 1))
        random.shuffle(options)
        choice = st.radio("정답을 선택하세요:", options, index=None)
    else:
        choice = st.text_input("영문 용어를 입력하세요:").strip() or None

    # 정답 확인
    confirm = st.button("정답 확인") or (st.session_state.mode == "주관식 (직접 입력)" and choice)

    if confirm and not st.session_state.answered:
        st.session_state.answered = True
        result = check_answer(choice, ans, st.session_state.mode)

        if result is None:
            st.session_state.feedback = "⚠️ 먼저 정답을 입력하거나 선택하세요!"
        elif result:
            st.session_state.feedback = "✅ 정답입니다!"
            st.session_state.score += 1
        else:
            st.session_state.feedback = f"❌ 오답입니다. 정답은 [{ans}] 입니다."
            st.session_state.wrong_list.append({"문제": q, "정답": ans, "내답": choice})

    # 피드백 표시
    if st.session_state.feedback:
        if st.session_state.feedback.startswith("✅"):
            st.success(st.session_state.feedback)
        elif st.session_state.feedback.startswith("❌"):
            st.error(st.session_state.feedback)
        else:
            st.warning(st.session_state.feedback)

    # 다음 문제로
    if st.session_state.answered and st.button("➡️ 다음 문제"):
        st.session_state.cur_idx += 1
        st.session_state.feedback = ""
        st.session_state.answered = False
        st.session_state.q_data = None
        st.rerun()


# ==============================
# 📊 결과 화면
# ==============================
if st.session_state.phase == "result":
    st.success("🎉 퀴즈 완료!")
    total = len(st.session_state.terms)
    score = st.session_state.score
    rate = score / total * 100
    st.write(f"총 {total}문제 중 {score}개 정답 ✅")
    st.write(f"정답률: {rate:.1f}%")

    if st.session_state.wrong_list:
        if st.button("📘 오답 확인"):
            st.session_state.phase = "review"
            st.rerun()

    if st.button("🔁 다시 하기"):
        for key in default_state:
            st.session_state[key] = default_state[key]
        st.rerun()


# ==============================
# 🧾 오답 복습
# ==============================
if st.session_state.phase == "review":
    st.error("📘 오답 노트")
    for i, item in enumerate(st.session_state.wrong_list, 1):
        st.markdown(f"**{i}. {item['문제']}**")
        st.write(f"👉 정답: {item['정답']}")
        st.write(f"❌ 내 답: {item['내답']}")
        st.divider()

    if st.button("🔁 다시 하기"):
        for key in default_state:
            st.session_state[key] = default_state[key]
        st.rerun()