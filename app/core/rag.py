from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.core.memory_bank import MemoryBank
from app.db.vector_store import get_vector_store

SYSTEM_PROMPT = """당신은 다이어트 식품 전문 상담사입니다.
주어진 컨텍스트를 기반으로 사용자의 질문에 정확하고 도움이 되는 답변을 제공하세요.

{user_context}

참고 문서:
{context}

답변 규칙:
- 컨텍스트에 있는 정보만을 기반으로 답변하세요.
- 정보가 부족하면 솔직하게 모른다고 말하세요.
- 출처가 있다면 함께 제공하세요.
- 사용자 프로필이 있다면 맞춤형 답변을 제공하세요.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{question}"),
])


def format_docs(docs) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def format_sources(docs) -> str:
    """검색된 문서의 출처 정보를 포맷팅."""
    seen = set()
    lines = []
    for doc in docs:
        source = doc.metadata.get("source_file", "알 수 없음")
        similarity = doc.metadata.get("similarity", 0)
        category = doc.metadata.get("category", "")
        key = f"{source}:{doc.metadata.get('chunk_index', 0)}"
        if key not in seen:
            seen.add(key)
            lines.append(f"  - {source} (유사도: {similarity:.3f}, 카테고리: {category})")
    return "\n".join(lines)


async def ask(question: str, user_id: str = "default") -> dict:
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.llm_model,
        openai_api_key=settings.openai_api_key,
    )

    # 벡터 검색
    vector_store = get_vector_store()
    docs = vector_store.hybrid_search(question, k=4)
    context = format_docs(docs)
    sources = format_sources(docs)

    # 사용자 메모리
    memory_bank = MemoryBank(user_id=user_id)
    user_context = await memory_bank.build_context()

    # LLM 호출
    chain = prompt | llm | StrOutputParser()
    answer = await chain.ainvoke({
        "context": context,
        "user_context": user_context,
        "question": question,
    })

    return {"answer": answer, "sources": sources}


async def ask_stream(question: str, user_id: str = "default"):
    """스트리밍 응답을 위한 async generator."""
    settings = get_settings()
    llm = ChatOpenAI(
        model=settings.llm_model,
        openai_api_key=settings.openai_api_key,
        streaming=True,
    )

    # 벡터 검색
    vector_store = get_vector_store()
    docs = vector_store.hybrid_search(question, k=4)
    context = format_docs(docs)
    sources = format_sources(docs)

    # 사용자 메모리
    memory_bank = MemoryBank(user_id=user_id)
    user_context = await memory_bank.build_context()

    # LLM 스트리밍
    chain = prompt | llm | StrOutputParser()
    async for chunk in chain.astream({
        "context": context,
        "user_context": user_context,
        "question": question,
    }):
        yield chunk

    # 마지막에 출처 전송
    yield f"\n\n[SOURCES]{sources}[/SOURCES]"
