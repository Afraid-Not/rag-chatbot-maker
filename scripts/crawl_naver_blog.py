"""네이버 블로그 다이어트/건강 관련 크롤링 스크립트"""
import re
import time
from pathlib import Path
from urllib.parse import quote, unquote

import httpx
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent.parent / "data" / "naver_blog"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KEYWORDS = [
    # 2차 크롤링 키워드
    "다이어트 도시락 추천",
    "다이어트 샐러드 레시피",
    "곤약 다이어트 효과",
    "닭가슴살 다이어트 요리",
    "다이어트 스무디 레시피",
    "키토제닉 식단 음식",
    "간헐적 단식 식단",
    "다이어트 야식 추천",
    "다이어트 빵 저칼로리",
    "프로틴 쉐이크 다이어트",
    "귀리 오트밀 다이어트",
    "다이어트 중 외식 메뉴",
    "저염식 다이어트 식단",
    "다이어트 곡물 통곡물",
    "체지방 줄이는 음식",
    "포만감 높은 다이어트 음식",
    "다이어트 유제품 추천",
    "비건 다이어트 식단",
    "저당 다이어트 간식",
    "다이어트 수프 레시피",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": "https://search.naver.com/",
}

PER_KEYWORD = 10


def search_naver_blog(keyword: str, display: int = 10) -> list[dict]:
    """네이버 블로그 검색 결과에서 블로그 URL 추출"""
    encoded = quote(keyword)
    url = f"https://search.naver.com/search.naver?where=blog&query={encoded}&sm=tab_opt&nso=so%3Ar%2Cp%3A1y"

    results = []
    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=15) as client:
            resp = client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 블로그 검색 결과에서 링크 추출
        links = soup.select("a.title_link") or soup.select("a[class*='title']")
        if not links:
            # fallback: 모든 blog.naver.com 링크
            links = soup.find_all("a", href=re.compile(r"blog\.naver\.com"))

        seen = set()
        for link in links:
            href = link.get("href", "")
            if "blog.naver.com" not in href:
                continue
            # 중복 제거
            if href in seen:
                continue
            seen.add(href)
            title = link.get_text(strip=True) or "제목없음"
            results.append({"url": href, "title": title})
            if len(results) >= display:
                break

    except Exception as e:
        print(f"    검색 실패: {keyword} - {e}")

    return results


def extract_blog_id_and_log(url: str) -> tuple[str, str] | None:
    """블로그 URL에서 blogId와 logNo 추출"""
    # blog.naver.com/username/12345 패턴
    m = re.search(r"blog\.naver\.com/([^/?]+)/(\d+)", url)
    if m:
        return m.group(1), m.group(2)

    # blogId=xxx&logNo=xxx 패턴
    m_id = re.search(r"blogId=([^&]+)", url)
    m_log = re.search(r"logNo=(\d+)", url)
    if m_id and m_log:
        return m_id.group(1), m_log.group(1)

    return None


def crawl_blog_post(url: str) -> str | None:
    """네이버 블로그 포스트의 본문 텍스트 추출 (모바일 버전 사용)"""
    parsed = extract_blog_id_and_log(url)
    if not parsed:
        return None

    blog_id, log_no = parsed
    mobile_url = f"https://m.blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"

    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=15) as client:
            resp = client.get(mobile_url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # 본문 영역 찾기 (여러 선택자 시도)
        content = (
            soup.select_one("div.se-main-container")
            or soup.select_one("div#postViewArea")
            or soup.select_one("div.post_ct")
            or soup.select_one("div[class*='post']")
        )

        if content:
            # 불필요한 요소 제거
            for tag in content(["script", "style", "button", "svg"]):
                tag.decompose()
            text = content.get_text(separator="\n", strip=True)
            if len(text) > 100:  # 너무 짧은 건 스킵
                return text

        # fallback: body 전체
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        if len(text) > 200:
            return text

        return None

    except Exception:
        return None


def sanitize_filename(s: str) -> str:
    """파일명에 사용 불가능한 문자 제거"""
    s = re.sub(r'[\\/*?:"<>|]', "", s)
    s = s.strip()[:80]
    return s or "untitled"


if __name__ == "__main__":
    print("=" * 60)
    print("네이버 블로그 다이어트/건강 크롤링 시작")
    print(f"키워드: {len(KEYWORDS)}개, 키워드당 최대 {PER_KEYWORD}개")
    print("=" * 60)

    total_saved = 0
    total_tried = 0

    for i, keyword in enumerate(KEYWORDS, 1):
        print(f"\n[{i}/{len(KEYWORDS)}] 키워드: '{keyword}'")

        posts = search_naver_blog(keyword, display=PER_KEYWORD)
        print(f"  검색 결과: {len(posts)}개")

        for j, post in enumerate(posts, 1):
            total_tried += 1
            title = post["title"]
            url = post["url"]

            print(f"  ({j}/{len(posts)}) {title[:50]}...")
            text = crawl_blog_post(url)

            if text and len(text) > 100:
                safe_title = sanitize_filename(title)
                filename = f"{keyword.replace(' ', '_')}_{j:02d}_{safe_title}.txt"
                filepath = DATA_DIR / filename

                output = f"제목: {title}\nURL: {url}\n키워드: {keyword}\n수집일: {time.strftime('%Y-%m-%d')}\n{'='*80}\n\n{text}"
                filepath.write_text(output, encoding="utf-8")

                total_saved += 1
                print(f"    -> 저장 ({len(text):,} chars)")
            else:
                print(f"    -> 본문 추출 실패, 스킵")

            time.sleep(0.5)

        time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"완료! {total_saved}/{total_tried}개 저장")
    print(f"저장 위치: {DATA_DIR}")
