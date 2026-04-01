"""다이어트 식품 데이터 크롤링 스크립트 - 원본 텍스트 그대로 저장"""
import os
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent.parent / "data"
PDF_DIR = DATA_DIR / "pdf"
TEXT_DIR = DATA_DIR / "raw"

DATA_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)
TEXT_DIR.mkdir(exist_ok=True)

# 크롤링 대상 웹 페이지 목록
WEB_PAGES = [
    # 한국어 소스
    {
        "url": "https://namu.wiki/w/%EB%8B%A4%EC%9D%B4%EC%96%B4%ED%8A%B8/%EB%8F%84%EC%9B%80%EC%9D%B4%20%EB%90%98%EB%8A%94%20%EC%9D%8C%EC%8B%9D",
        "filename": "kr_namuwiki_diet_foods.txt",
        "desc": "나무위키 - 다이어트 도움이 되는 음식",
    },
    {
        "url": "https://www.hihealth.co.kr/foodinfo/?idx=2690146&bmode=view",
        "filename": "kr_hihealth_high_protein_15.txt",
        "desc": "고단백 저칼로리 식품 15가지",
    },
    {
        "url": "https://news.hidoc.co.kr/news/articleView.html?idxno=1136",
        "filename": "kr_hidoc_low_cal_top10.txt",
        "desc": "하이닥 - 저칼로리 음식 Best 10",
    },
    {
        "url": "https://kormedi.com/1605207/",
        "filename": "kr_kormedi_low_cal_foods.txt",
        "desc": "코메디닷컴 - 칼로리 낮아도 든든한 식품들",
    },
    {
        "url": "https://www.wkorea.com/2025/11/24/%EC%98%81%EC%96%91%EC%82%AC%EA%B0%80-%EA%BC%BD%EC%9D%80-%EB%8B%A4%EC%9D%B4%EC%96%B4%ED%8A%B8-%EC%B5%9C%EA%B3%A0%EC%9D%98-%EC%8B%9D%ED%92%88-8",
        "filename": "kr_wkorea_nutritionist_top8.txt",
        "desc": "W Korea - 영양사가 꼽은 다이어트 식품 8",
    },
    {
        "url": "https://www.dietshin.com/calorie/calorie_main.asp",
        "filename": "kr_dietshin_calorie_dict.txt",
        "desc": "다이어트신 - 음식 칼로리 사전",
    },
    {
        "url": "https://my-doctor.io/healthLab/info/1404/%EB%8B%A4%EC%9D%B4%EC%96%B4%ED%8A%B8-%EC%A0%80%EC%B9%BC%EB%A1%9C%EB%A6%AC-%EC%8B%9D%EB%8B%A8-%EA%B5%AC%EC%84%B1%EB%B2%95",
        "filename": "kr_mydoctor_low_cal_diet_plan.txt",
        "desc": "저칼로리 식단 구성법",
    },
    # 영어 소스
    {
        "url": "https://www.healthline.com/nutrition/most-weight-loss-friendly-foods",
        "filename": "en_healthline_weight_loss_foods.txt",
        "desc": "Healthline - 16 Weight Loss Friendly Foods",
    },
    {
        "url": "https://www.seasonhealth.com/blog/high-volume-low-calorie-foods",
        "filename": "en_season_high_volume_low_cal.txt",
        "desc": "Season Health - 28 High-Volume Low-Cal Foods",
    },
    {
        "url": "https://www.myfooddata.com/articles/low-calorie-foods.php",
        "filename": "en_myfooddata_low_cal_10.txt",
        "desc": "MyFoodData - 10 Best Low Calorie Foods",
    },
    {
        "url": "https://www.mayoclinic.org/healthy-lifestyle/weight-loss/in-depth/weight-loss/art-20044318",
        "filename": "en_mayoclinic_weight_loss.txt",
        "desc": "Mayo Clinic - Feel Full on Fewer Calories",
    },
    {
        "url": "https://www.cdc.gov/healthy-weight-growth/healthy-eating/index.html",
        "filename": "en_cdc_healthy_eating.txt",
        "desc": "CDC - Healthy Eating Tips",
    },
    {
        "url": "https://www.health.harvard.edu/diet-and-nutrition/creating-balanced-healthy-meals-from-low-calorie-nutrient-dense-foods",
        "filename": "en_harvard_balanced_meals.txt",
        "desc": "Harvard Health - Balanced Healthy Meals",
    },
]

# PDF 다운로드 목록
PDF_URLS = [
    {
        "url": "https://www.mfds.go.kr/webzine/201305/pdf/08.pdf",
        "filename": "kr_mfds_diet_food_guide.pdf",
        "desc": "식약처 - 체중조절용 조제식품 가이드",
    },
    {
        "url": "https://www.mfds.go.kr/webzine/201009/10sep_pdf/14.pdf",
        "filename": "kr_mfds_nutrition_label.pdf",
        "desc": "식약처 - 영양성분표 가이드",
    },
    {
        "url": "https://health.ucdavis.edu/transplant/PDFs/Helpful%20Guidelines%20for%20Successful%20Weight%20Loss.pdf",
        "filename": "en_ucdavis_weight_loss_guide.pdf",
        "desc": "UC Davis - Weight Loss Guidelines",
    },
    {
        "url": "https://www.brighamandwomens.org/assets/BWH/cwmw/pdfs/cwmw-medical-weight-management.pdf",
        "filename": "en_brigham_weight_management.pdf",
        "desc": "Brigham - Medical Weight Management Nutrition Guide",
    },
    {
        "url": "https://wexnermedical.osu.edu/-/media/files/wexnermedical/patient-care/healthcare-services/nutrition-services/nutrition-and-education/healthy-meals-for-weight-loss.pdf",
        "filename": "en_osu_healthy_meals_weight_loss.pdf",
        "desc": "OSU - Healthy Meals for Weight Loss",
    },
    {
        "url": "https://health.students.vcu.edu/media/student-affairs-sites/ushs/docs/Weightlossguide.pdf",
        "filename": "en_vcu_practical_weight_loss_guide.pdf",
        "desc": "VCU - Practical Guide to Healthy Weight Loss",
    },
    {
        "url": "https://www.nhlbi.nih.gov/sites/default/files/publications/14-7415.pdf",
        "filename": "en_nhlbi_healthy_weight_pocket_guide.pdf",
        "desc": "NHLBI - Healthy Weight Pocket Guide",
    },
    {
        "url": "https://cdn.who.int/media/docs/default-source/searo/ncd/ncd-flip-charts/2.-healthy-diet-24-04-19.pdf",
        "filename": "en_who_healthy_diet.pdf",
        "desc": "WHO - Healthy Diet Guide",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


def extract_text(html: str) -> str:
    """HTML에서 본문 텍스트를 그대로 추출"""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def crawl_page(url: str, filename: str, desc: str) -> bool:
    """웹 페이지를 크롤링하여 원본 텍스트를 저장"""
    try:
        print(f"  크롤링 중: {desc}")
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30) as client:
            resp = client.get(url)
            resp.raise_for_status()

        text = extract_text(resp.text)

        # 메타 정보 + 원본 텍스트 저장
        output = f"URL: {url}\n수집일: {time.strftime('%Y-%m-%d')}\n설명: {desc}\n{'='*80}\n\n{text}"

        filepath = TEXT_DIR / filename
        filepath.write_text(output, encoding="utf-8")
        print(f"  ✓ 저장 완료: {filepath} ({len(text):,} chars)")
        return True

    except Exception as e:
        print(f"  ✗ 실패: {desc} - {e}")
        return False


def download_pdf(url: str, filename: str, desc: str) -> bool:
    """PDF 파일 다운로드"""
    try:
        print(f"  다운로드 중: {desc}")
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=60) as client:
            resp = client.get(url)
            resp.raise_for_status()

        filepath = PDF_DIR / filename
        filepath.write_bytes(resp.content)
        size_kb = len(resp.content) / 1024
        print(f"  ✓ 저장 완료: {filepath} ({size_kb:.1f} KB)")
        return True

    except Exception as e:
        print(f"  ✗ 실패: {desc} - {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("다이어트 식품 데이터 크롤링 시작")
    print("=" * 60)

    # 웹 페이지 크롤링
    print(f"\n[1/2] 웹 페이지 크롤링 ({len(WEB_PAGES)}개)")
    web_success = 0
    for page in WEB_PAGES:
        if crawl_page(page["url"], page["filename"], page["desc"]):
            web_success += 1
        time.sleep(1)

    # PDF 다운로드
    print(f"\n[2/2] PDF 다운로드 ({len(PDF_URLS)}개)")
    pdf_success = 0
    for pdf in PDF_URLS:
        if download_pdf(pdf["url"], pdf["filename"], pdf["desc"]):
            pdf_success += 1
        time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"완료! 웹: {web_success}/{len(WEB_PAGES)}, PDF: {pdf_success}/{len(PDF_URLS)}")
    print(f"저장 위치: {DATA_DIR}")
