# Time Trade App

Next.js와 Supabase를 사용한 시간 거래 애플리케이션입니다.

## 기술 스택

- **Frontend**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Database**: Supabase
- **Testing**: Playwright

## 시작하기

### 1. 의존성 설치

```bash
npm install
```

### 2. 환경 변수 설정

`.env.local` 파일을 수정하여 Supabase 프로젝트 정보를 입력하세요:

```env
NEXT_PUBLIC_SUPABASE_URL=your-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

Supabase 프로젝트 정보는 [Supabase 대시보드](https://app.supabase.com/project/_/settings/api)에서 확인할 수 있습니다.

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인하세요.

## 프로젝트 구조

```
.
├── app/                  # Next.js App Router 페이지
│   ├── layout.tsx       # 루트 레이아웃
│   ├── page.tsx         # 홈페이지
│   └── globals.css      # 전역 스타일
├── lib/                  # 유틸리티 및 설정
│   ├── supabase.ts      # 클라이언트 사이드 Supabase 클라이언트
│   └── supabase-server.ts # 서버 사이드 Supabase 클라이언트
└── .env.local           # 환경 변수 (gitignore됨)
```

## Supabase 사용법

### 클라이언트 컴포넌트에서 사용

```tsx
'use client'

import { supabase } from '@/lib/supabase'

export default function MyComponent() {
  // Supabase 사용 예시
  const fetchData = async () => {
    const { data, error } = await supabase.from('your_table').select('*')
  }

  return <div>...</div>
}
```

### 서버 컴포넌트에서 사용

```tsx
import { createServerClient } from '@/lib/supabase-server'

export default async function MyServerComponent() {
  const supabase = await createServerClient()
  const { data, error } = await supabase.from('your_table').select('*')

  return <div>...</div>
}
```

## 사용 가능한 명령어

```bash
npm run dev      # 개발 서버 실행
npm run build    # 프로덕션 빌드
npm run start    # 프로덕션 서버 실행
npm run lint     # ESLint 실행
```

## Claude Code MCP 통합

이 프로젝트는 Claude Code와 Supabase MCP (Model Context Protocol) 통합이 설정되어 있습니다.

### MCP 설정

Claude Code가 Supabase 데이터베이스와 직접 상호작용할 수 있도록 MCP 서버가 구성되어 있습니다:

- **MCP 서버**: `@supabase/mcp-server-supabase`
- **설정 위치**: `~/.claude.json` 파일의 프로젝트별 설정
- **환경 변수**: `.env.local`의 Supabase 자격 증명 사용

### 사용 방법

1. Claude Code를 재시작하여 MCP 서버를 로드합니다
2. Claude Code에서 `/mcp` 명령어로 연결된 MCP 서버 확인
3. Claude에게 데이터베이스 작업 요청:
   - 테이블 생성/조회
   - 데이터 CRUD 작업
   - 스키마 확인 및 수정

### 주의사항

- MCP 서버는 `.env.local`의 자격 증명을 사용합니다
- Supabase URL이나 키를 변경하면 `.claude.json` 파일도 함께 업데이트해야 합니다
- MCP 연결 문제 시 Claude Code 재시작이 필요할 수 있습니다

## 다음 단계

1. Supabase 대시보드에서 데이터베이스 스키마 설정
2. 인증(Authentication) 설정
3. API 라우트 및 서버 액션 구현
4. UI 컴포넌트 개발
