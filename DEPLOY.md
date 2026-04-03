# 배포 가이드 (Ngrok + Vercel)

## 구조

```
외부 사용자 --> Vercel (프론트엔드) --> Ngrok --> 내 PC (백엔드)
```

- **프론트엔드**: Vercel에 배포 (무료, 영구 URL)
- **백엔드**: 내 PC에서 실행, ngrok으로 외부 노출 (PC 켜져 있어야 함)

---

## 사전 준비 (최초 1회)

### 1. ngrok 설치 및 계정 연동

```bash
# https://dashboard.ngrok.com/signup 에서 가입 후 authtoken 복사
ngrok config add-authtoken <YOUR_TOKEN>
```

### 2. Vercel 로그인

```bash
npx vercel login
```

---

## 배포 실행 순서

### Step 1. 백엔드 실행

```bash
conda run -n rag-chatbot --no-capture-output python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2. ngrok 터널 열기 (새 터미널)

```bash
ngrok http 8000
```

터미널에 표시되는 URL 확인 (예: `https://xxxx-xxxx.ngrok-free.dev`)

### Step 3. Vercel 환경변수 업데이트 (ngrok URL이 바뀔 때마다)

```bash
# 기존 환경변수 삭제
npx vercel env rm NEXT_PUBLIC_API_URL production -y

# 새 ngrok URL로 등록
echo "https://xxxx-xxxx.ngrok-free.dev" | npx vercel env add NEXT_PUBLIC_API_URL production
```

### Step 4. Vercel 배포

```bash
cd frontend
npx vercel --prod --yes
```

배포 완료 후 출력되는 URL을 공유하면 끝.

---

## 공유 URL

- **프론트엔드** (공유용): `https://frontend-ten-sable-63.vercel.app`
- **백엔드 API**: ngrok URL (매번 변경됨)

---

## 주의사항

- ngrok 무료 플랜은 **재시작 시 URL이 변경**됨 --> Step 3~4 반복 필요
- 내 PC가 꺼지거나 ngrok을 종료하면 **외부 접속 불가**
- `app/main.py`의 CORS 설정이 `allow_origins=["*"]`인지 확인
- `frontend/src/lib/api.ts`에 `ngrok-skip-browser-warning` 헤더가 포함되어 있어야 함
