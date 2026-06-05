import re
import streamlit as st

st.set_page_config(page_title="어머니의 마음 가사 점검기", page_icon="🎵", layout="centered")

st.title("🎵 어머니의 마음 가사 점검기")
st.write("한 줄의 가사를 4마디로 나누어 입력하면 글자수와 말의 흐름을 점검합니다.")

st.markdown(
    """
    <style>
    .flow-wrap {
        margin: 1.1rem 0 1.5rem 0;
        padding: 1rem;
        border: 1px solid #8fb9dc;
        border-radius: 8px;
        background: #f7fbff;
    }
    .flow-title {
        font-weight: 700;
        color: #2f6690;
        margin-bottom: 0.7rem;
    }
    .flow-row {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        flex-wrap: wrap;
    }
    .flow-box {
        border: 1px solid #8fb9dc;
        border-radius: 6px;
        padding: 0.45rem 0.65rem;
        background: #ffffff;
        color: #1f3f5b;
        font-weight: 650;
        white-space: nowrap;
    }
    .flow-arrow {
        color: #5f92bd;
        font-weight: 800;
        font-size: 1.1rem;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        border: 2.5px solid #d71920;
        background-color: #ffffff;
        border-radius: 7px;
    }
    div[data-testid="stTextInput"] input {
        border: 2.5px solid #d71920;
        background-color: #ffffff;
        border-radius: 7px;
    }
    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
        border-color: #b51218;
        box-shadow: 0 0 0 3px rgba(215, 25, 32, 0.16);
    }
    div[data-testid="stButton"] button {
        border: 1px solid #2f6690;
        background: #2f6690;
        color: #ffffff;
        font-weight: 800;
        border-radius: 7px;
        padding: 0.45rem 1rem;
    }
    div[data-testid="stButton"] button:hover {
        border-color: #244f70;
        background: #244f70;
        color: #ffffff;
    }
    .rhythm-box {
        border: 1px solid #d8e0ea;
        border-radius: 8px;
        padding: 14px 16px;
        margin: 10px 0 18px 0;
        background: #f8fafc;
    }
    .rhythm-title {
        font-size: 17px;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 6px;
    }
    .rhythm-symbols {
        font-size: 24px;
        line-height: 1.6;
        color: #111827;
        letter-spacing: 0;
        word-break: keep-all;
    }
    .rhythm-counts {
        font-size: 16px;
        color: #4b5563;
        margin-top: 6px;
    }
    .triplet {
        display: inline-block;
        position: relative;
        padding-top: 0.8em;
        margin: 0 3px;
        vertical-align: baseline;
        line-height: 1;
    }
    .triplet-mark {
        position: absolute;
        top: 0.1em;
        left: 0.15em;
        right: 0.15em;
        height: 0.42em;
        border-top: 2px solid #111827;
        border-left: 2px solid #111827;
        border-right: 2px solid #111827;
        text-align: center;
    }
    .triplet-num {
        position: relative;
        top: -0.68em;
        font-size: 13px;
        line-height: 1;
        font-weight: 800;
        color: #111827;
    }
    .triplet-notes {
        line-height: 1;
    }
    </style>
    <div class="flow-wrap">
        <div class="flow-title">AI 가사 점검 흐름</div>
        <div class="flow-row">
            <div class="flow-box">줄 선택</div>
            <div class="flow-arrow">→</div>
            <div class="flow-box">가사 입력</div>
            <div class="flow-arrow">→</div>
            <div class="flow-box">글자수 점검</div>
            <div class="flow-arrow">→</div>
            <div class="flow-box">말 흐름 점검</div>
            <div class="flow-arrow">→</div>
            <div class="flow-box">자기 수정</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 줄별 기준 글자수
LINE_RULES = {
    1: [3, 4, 4, 2],
    2: [4, 4, 4, 1],
    3: [4, 4, 5, 1],
    4: [4, 5, 7, 1],
    5: [4, 4, 4, 1],
    6: [4, 5, 4, 1],
}

RHYTHM_CODES = {
    1: "444 / 6222 / 6222 / 84",
    2: "6222 / 6222 / 6222 / 8-4",
    3: "3144 / 3144 / 61122 / 8-4",
    4: "3144 / (222)44 / 2222211 / 8-4",
    5: "3144 / (222)8 / 6222 / 8-4",
    6: "2244 / (222)44 / 6222 / 8-4",
}

RHYTHM_SYMBOLS = {
    "1": "𝅘𝅥𝅯",
    "2": "♪",
    "3": "♪.",
    "4": "♩",
    "6": "♩.",
    "8": "𝅗𝅥",
}


def rhythm_to_symbols(code: str) -> str:
    """숫자 리듬코드를 학생이 볼 리듬꼴 기호로 바꾼다."""
    bars = []

    for bar in code.split("/"):
        bar = bar.strip()
        symbols = []
        i = 0

        while i < len(bar):
            ch = bar[i]

            if ch == "(":
                close = bar.find(")", i)
                if close != -1:
                    inner = rhythm_to_symbols(bar[i + 1:close])
                    symbols.append(
                        f'<span class="triplet"><span class="triplet-mark"><span class="triplet-num">3</span></span>'
                        f'<span class="triplet-notes">{inner}</span></span>'
                    )
                    i = close + 1
                    continue

            if ch == "-":
                if i + 1 < len(bar) and bar[i + 1] == "4":
                    symbols.append("𝄽")
                    i += 2
                else:
                    symbols.append("-")
                    i += 1
                continue

            if ch in RHYTHM_SYMBOLS:
                symbol = RHYTHM_SYMBOLS[ch]
                if i + 1 < len(bar) and bar[i + 1] == ".":
                    if not symbol.endswith("."):
                        symbol += "."
                    i += 1
                symbols.append(symbol)

            i += 1

        bars.append(" ".join(symbols))

    return " / ".join(bars)

# 세션 저장
if "saved_lines" not in st.session_state:
    st.session_state.saved_lines = {i: "" for i in range(1, 7)}

# -----------------------------
# 기본 함수
# -----------------------------

def count_chars(text: str) -> int:
    """한글과 하이픈만 글자수로 센다."""
    return sum(1 for ch in text if ch == "-" or "가" <= ch <= "힣")


def counted_text(text: str) -> str:
    """글자수 계산에 실제로 사용한 글자만 남긴다."""
    return "".join(ch for ch in text if ch == "-" or "가" <= ch <= "힣")


def meaning_text(text: str) -> str:
    """말 흐름 판단용: 하이픈과 문장부호를 빼고 한글만 남긴다."""
    return "".join(ch for ch in text if "가" <= ch <= "힣")


def normalize_line(parts) -> str:
    return "/".join(part.strip() for part in parts)


# -----------------------------
# 말 흐름 점검
# -----------------------------

def third_madi_warning(parts) -> str | None:
    """2마디와 3마디 사이에서 수정이 필요한 흐름을 점검한다."""
    third = meaning_text(parts[2].strip())
    if not third:
        return None

    # '고'가 단어 첫 글자인 경우는 제외
    safe_starts = [
        "고생", "고마", "고맙", "고운", "고된", "고요",
        "가족", "가득", "가장", "가끔",
        "이제", "이런", "이렇게", "이만",
    ]
    if any(third.startswith(word) for word in safe_starts):
        return None

    # 3마디 첫머리에 오면 어색할 수 있는 조사·어미
    weak_starts = [
        "에게", "한테", "으로", "께",
        "는", "은", "이", "가", "를", "을", "에", "도", "의", "와", "과", "로",
        "고", "며", "서", "니", "다", "요",
    ]
    weak_starts = sorted(weak_starts, key=len, reverse=True)

    for word in weak_starts:
        if third.startswith(word):
            return f"3마디가 ‘{word}’로 시작해요. ‘우리집에서’처럼 앞말에 붙어야 자연스러운 말입니다. 이 부분은 고쳐 보는 것이 좋습니다."

    return None


def expression_feedback(parts, line_num: int) -> dict[str, list[str]]:
    """글자수는 맞지만 말 흐름상 수정할 부분과 다시 살펴볼 부분을 나누어 안내한다."""
    strong_warnings = []
    soft_warnings = []
    joined = "".join(meaning_text(part) for part in parts)

    warning = third_madi_warning(parts)
    if warning:
        strong_warnings.append(warning)

    if "엄마빠" in joined:
        strong_warnings.append("‘엄마빠’는 줄임말처럼 들릴 수 있어요. 같은 4글자인 ‘엄마아빠’로 고쳐 부르는 것이 좋습니다.")

    # 1~2줄은 도입이므로 정서 판단을 약하게 한다.
    # 5~6줄은 마무리이므로 마음 표현이 전혀 없으면 짧게 안내한다.
    emotion_words = ["감사", "고마", "고맙", "사랑", "존경", "미안", "소중", "행복", "마음", "효도"]
    has_emotion = any(word in joined for word in emotion_words)

    if line_num in [5, 6] and not has_emotion:
        soft_warnings.append("마무리 부분에서는 감사, 사랑, 고마움 같은 마음이 조금 더 드러나면 좋아요.")
    elif line_num in [3, 4] and not has_emotion:
        soft_warnings.append("중간 부분이므로 가족에게 전하고 싶은 마음이 조금 더 드러나면 좋아요.")

    return {
        "strong": strong_warnings,
        "soft": soft_warnings,
    }


# -----------------------------
# 입력 영역
# -----------------------------

line_num = st.selectbox("점검할 줄을 선택하세요", [1, 2, 3, 4, 5, 6])
st.markdown(
    f"""
    <div class="rhythm-box">
        <div class="rhythm-title">{line_num}줄 리듬</div>
        <div class="rhythm-symbols">{rhythm_to_symbols(RHYTHM_CODES[line_num])}</div>
        <div class="rhythm-counts">기준 글자수: {' / '.join(map(str, LINE_RULES[line_num]))}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

lyrics = st.text_input("가사를 입력하세요", placeholder="예: 앞-으로/엄마아빠/께효도하면/서")

if st.button("검사하기"):
    rules = LINE_RULES[line_num]
    parts = [p.strip() for p in lyrics.split("/")]

    st.subheader(f"🎵 {line_num}줄 점검 결과")

    # 1. 마디 수 검사
    if len(parts) != 4:
        st.error("/ 표시로 4마디가 되도록 다시 나누어 써 주세요.")
        st.stop()

    # 2. 글자수 검사
    errors = []
    counts = []

    for i, part in enumerate(parts):
        target = rules[i]
        current = count_chars(part)
        real = counted_text(part)
        counts.append(current)

        if real.startswith("-"):
            errors.append(f"{i+1}마디는 하이픈(-)으로 시작하면 안 돼요.")

        if current != target:
            if current < target:
                errors.append(f"{i+1}마디 ‘{part}’는 기준 {target}글자인데 현재 {current}글자라 {target-current}글자 부족해요.")
            else:
                errors.append(f"{i+1}마디 ‘{part}’는 기준 {target}글자인데 현재 {current}글자라 {current-target}글자 많아요.")

    # 3. 글자수 오류가 있으면 여기서 끝낸다.
    if errors:
        st.error("글자수 수정이 필요해요.")
        st.markdown("### 🔴 먼저 고칠 곳")
        for error in errors:
            st.write("- " + error)
        st.markdown("### ✏️ 수정 방향")
        st.write("먼저 기준 글자수에 맞게 다시 고쳐 보세요.")
        st.stop()

    # 4. 글자수 통과
    st.success(f"글자수는 맞아요. 기준 {'/'.join(map(str, rules))}에 맞게 썼어요.")

    # 5. 아주 짧은 마디별 확인
    with st.expander("마디별 글자수 보기"):
        for i, part in enumerate(parts):
            st.write(f"{i+1}마디: {part}  —  기준 {rules[i]}글자 / 현재 {counts[i]}글자")

    # 6. 말 흐름과 가사 기능 확인
    feedback = expression_feedback(parts, line_num)

    if feedback["strong"]:
        st.markdown("### 🟠 수정을 권하는 곳")
        st.warning("말의 흐름이 어색하게 들릴 수 있어요. 아래 부분은 고쳐 보는 것이 좋습니다.")
        for warning in feedback["strong"]:
            st.write("- " + warning)

    if feedback["soft"]:
        st.markdown("### 🟡 다시 불러볼 곳")
        for warning in feedback["soft"]:
            st.write("- " + warning)

    if not feedback["strong"] and not feedback["soft"]:
        st.info("말 흐름에 크게 어색한 부분은 없어 보여요.")

    # 7. 임시 저장
    st.session_state.saved_lines[line_num] = normalize_line(parts)

    st.markdown("### ➡️ 다음 입력")
    if line_num < 6:
        st.write(f"{line_num + 1}줄 내용을 넣으세요.")
    else:
        st.write("6줄까지 점검했습니다. 전체 가사를 이어서 불러 보며 자연스러운지 확인해 보세요.")

# -----------------------------
# 저장된 가사 표시
# -----------------------------

if any(st.session_state.saved_lines.values()):
    st.divider()
    st.subheader("🎼 지금까지 입력한 가사")
    for i in range(1, 7):
        text = st.session_state.saved_lines.get(i, "")
        if text:
            st.write(f"{i}줄: {text}")
        else:
            st.write(f"{i}줄: ")
