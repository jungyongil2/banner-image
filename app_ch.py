import os
import random
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
from openai import OpenAI

# ✅ GPT API Key 직접 입력
client = OpenAI(api_key="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")  # 본인 키로 교체하세요

# ✅ 경로 설정
BASE_DIR = os.path.dirname(__file__)
IMAGE_DIR = os.path.join(BASE_DIR, "images")
FONT_PATH = os.path.join(BASE_DIR, "NanumGothic.ttf")  # 폰트도 동일하게

CHARACTER_PATHS = {
    "곰캐릭터": os.path.join(IMAGE_DIR, "bear_character"),
    "새캐릭터": os.path.join(IMAGE_DIR, "bird_character"),
    "펭귄캐릭터": os.path.join(IMAGE_DIR, "penguin_character")
}

BANNER_SIZE = {
    "카카오 알림톡 배너": (1000, 300),
    "홈 배너": (1000, 300),
    "홈 배너 (세로)": (600, 800),
}

BANNER_BACKGROUND = {
    "카카오 알림톡 배너": "#2E3192",
    "홈 배너": "#E3F2FA",
    "홈 배너 (세로)": "#FFFFFF"
}

def wrap_text(text, font, max_width):
    lines, words, current_line = [], text.split(" "), ""
    for word in words:
        test_line = current_line + word + " "
        if font.getlength(test_line) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    lines.append(current_line.strip())
    return lines

def extract_lines(content):
    headline, subtext = "", ""
    for line in content:
        if "헤드라인" in line:
            headline = line.split(":", 1)[-1].strip()
        elif "설명" in line or "부가 설명" in line:
            subtext = line.split(":", 1)[-1].strip()
    return headline, subtext

def generate_marketing_text(product, rate, feature):
    prompt = f"""
당신은 은행 상품 마케팅 문구를 생성하는 전문가입니다.

- 상품명: {product}
- 금리: {rate}
- 특징: {feature}

아래 형식으로 출력해 주세요. 반드시 두 줄로 출력하고, 라벨과 내용 사이에 ':'를 포함하세요.

헤드라인: (20자 이내로 후킹 있게 작성)
설명: (30자 이내로 혜택 설명)"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=150
        )
        content = response.choices[0].message.content.strip().split("\\n" if "\\n" in response.choices[0].message.content else "\n")
        headline, subtext = extract_lines(content)
    except Exception as e:
        st.error(f"GPT 생성 실패: {e}")
        headline = f"{product} 지금 시작하세요!"
        subtext = feature
    return headline or f"{product} 지금 시작!", subtext or feature

def create_banner(banner_type, character, headline, subtext):
    width, height = BANNER_SIZE[banner_type]
    bg_color = BANNER_BACKGROUND[banner_type]
    banner = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(banner)

    title_font = ImageFont.truetype(FONT_PATH, 44 if height > width else 40)
    sub_font = ImageFont.truetype(FONT_PATH, 32 if height > width else 28)

    max_text_width = width - 400 if height <= width else width - 120
    headline_wrapped = wrap_text(headline, title_font, max_text_width)
    subtext_wrapped = wrap_text(subtext, sub_font, max_text_width)
    all_lines = headline_wrapped + subtext_wrapped
    total_text_height = len(all_lines) * (title_font.size + 10)

    char_folder = CHARACTER_PATHS[character]
    images = [f for f in os.listdir(char_folder) if f.endswith((".png", ".jpg"))]
    char_img = None
    if images:
        img_path = os.path.join(char_folder, random.choice(images))
        char_img = Image.open(img_path).convert("RGBA")
        size = (220, 220) if height > width else (280, 280)
        char_img = char_img.resize(size)

    if banner_type == "홈 배너":
        if char_img:
            banner.paste(char_img, (40, height - size[1] - 20), char_img)
        text_x = 320
        text_y = 80
        for line in headline_wrapped:
            draw.text((text_x, text_y), line, font=title_font, fill="black")
            text_y += title_font.size + 10
        for line in subtext_wrapped:
            draw.text((text_x, text_y), line, font=sub_font, fill="black")
            text_y += sub_font.size + 6

    elif banner_type == "홈 배너 (세로)":
        y = int((height - total_text_height) / 2.5)
        for line in all_lines:
            font = title_font if line in headline_wrapped else sub_font
            line_width = font.getlength(line)
            x = int((width - line_width) / 2)
            draw.text((x, y), line, font=font, fill="black")
            y += font.size + 10
        if char_img:
            banner.paste(char_img, (int((width - size[0]) / 2), height - size[1] - 40), char_img)

    else:
        text_x, text_y = 60, 80
        for line in headline_wrapped:
            draw.text((text_x, text_y), line, font=title_font, fill="white")
            text_y += title_font.size + 10
        for line in subtext_wrapped:
            draw.text((text_x, text_y), line, font=sub_font, fill="white")
            text_y += sub_font.size + 6
        if char_img:
            banner.paste(char_img, (width - size[0] - 40, height - size[1] - 20), char_img)

    return banner

# ✅ Streamlit UI
st.set_page_config(layout="wide")
st.title("🐧 GPT 문구 안정적 생성 배너 생성기")

col1, col2 = st.columns([1, 2])
with col1:
    banner_type = st.selectbox("배너형태", list(BANNER_SIZE.keys()))
    character = st.selectbox("캐릭터 선택", list(CHARACTER_PATHS.keys()))
    use_gpt = st.radio("문구 생성 방식", ["GPT 자동 생성", "직접 입력"])

with col2:
    product = st.text_input("상품명", "모두의 적금")
    rate = st.text_input("금리", "최대 연 7%")
    feature = st.text_area("상품 특징", "급여이체, 연금수령, 가맹점결제계좌 중 하나만 있어도 혜택!")

if use_gpt == "GPT 자동 생성":
    headline, subtext = generate_marketing_text(product, rate, feature)
    st.markdown(f"🧠 **헤드라인:** {headline}")
    st.markdown(f"🧠 **설명:** {subtext}")
else:
    headline = st.text_input("헤드라인 입력", product + " 지금 시작하세요!")
    subtext = st.text_input("부가 설명 입력", feature)

if st.button("🎯 배너 생성"):
    banner = create_banner(banner_type, character, headline, subtext)
    st.subheader("🖼️ 최종 배너 미리보기")
    st.image(banner, use_column_width=False, width=600)

    output_path = os.path.join(BASE_DIR, "final_banner.png")
    banner.save(output_path)
    with open(output_path, "rb") as f:
        st.download_button("📥 배너 다운로드", f, file_name="banner.png") 
