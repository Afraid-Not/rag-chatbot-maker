import httpx
from bs4 import BeautifulSoup


async def fetch_page(url: str) -> str:
    """URL에서 HTML을 가져온다."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        return response.text


def extract_text(html: str) -> str:
    """HTML에서 본문 텍스트를 추출한다."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    return soup.get_text(separator="\n", strip=True)


async def crawl(url: str) -> str:
    """URL을 크롤링하여 텍스트를 반환한다."""
    html = await fetch_page(url)
    return extract_text(html)
