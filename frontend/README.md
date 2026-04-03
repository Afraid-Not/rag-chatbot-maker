# Diet Food RAG Chatbot — Frontend

다이어트 식품 전문 AI 상담 챗봇의 프론트엔드 애플리케이션. FastAPI 백엔드의 RAG 파이프라인과 SSE 스트리밍으로 연동됩니다.

## Features

- SSE 기반 실시간 스트리밍 응답
- 다중 채팅 세션 관리 (localStorage 저장)
- Markdown 렌더링 및 출처 토글
- 사용자 메모리 뱅크 (조회/저장/삭제)
- Vercel + ngrok 기반 외부 배포 지원

## Tech Stack

- **Next.js 16** (App Router)
- **React 19**
- **Tailwind CSS v4** + `@tailwindcss/typography`
- **shadcn/ui** (Button, ScrollArea, Separator, Sheet)
- **react-markdown** (응답 렌더링)
- **Geist** font

## Project Structure

```
src/
├── app/
│   ├── layout.tsx          # Root layout (ko, Geist font)
│   ├── page.tsx            # Main chat page
│   └── globals.css         # Tailwind global styles
├── components/
│   ├── chat-input.tsx      # 메시지 입력 폼
│   ├── chat-panel.tsx      # 채팅 메시지 영역 + 자동 스크롤
│   ├── message-bubble.tsx  # 메시지 버블 (마크다운 + 출처)
│   ├── memory-panel.tsx    # 사이드바 메모리 뱅크 패널
│   ├── session-sidebar.tsx # 세션 목록 사이드바
│   └── ui/                 # shadcn/ui 컴포넌트
└── lib/
    ├── api.ts              # 백엔드 API 클라이언트 (SSE 스트림, 메모리 CRUD)
    ├── sessions.ts         # localStorage 세션 관리
    ├── types.ts            # Message, Session 타입 정의
    └── utils.ts            # cn() 유틸리티
```

## Getting Started

### Prerequisites

- Node.js 24+
- 백엔드 서버 실행 중 (FastAPI, 기본 포트 12351)

### Installation

```bash
npm install
```

### Development

```bash
npm run dev -- --webpack --port 12350
```

> Windows에서 Turbopack CSS 크래시 발생 시 `--webpack` 플래그를 사용하세요.

### Production Build

```bash
npm run build
npm start
```

## Environment Variables

`.env.local` 파일에 설정:

```
NEXT_PUBLIC_API_URL=http://localhost:12351
```

외부 배포 시 ngrok URL로 변경:

```
NEXT_PUBLIC_API_URL=https://xxxx.ngrok-free.dev
```

## Deployment

Vercel에 배포됨: https://rag-chatbot-20260403.vercel.app

```bash
npx vercel --prod --yes
```

배포 구조: `Vercel (프론트) → ngrok → 로컬 PC (백엔드)`

자세한 내용은 루트의 `DEPLOY.md` 참고.
