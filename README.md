# 사통팔땅 (SatongPalTang)

**다중테넌트 부동산 개발사업 통합관리 SaaS 플랫폼**

부동산 개발·시행·분양 전 과정을 하나의 클라우드에서 관리하는 멀티테넌트 SaaS 플랫폼입니다.
사업자(테넌트)별로 현장·직원·계약·회계·수지·공정·토지·리츠 정보를 통합 관리하며,
하나의 중앙 플랫폼에서 모든 현장을 제어·운영할 수 있습니다.

## 🎯 주요 기능

### 핵심 모듈

- **🏢 테넌트 관리**: 멀티테넌트 아키텍처, 구독 관리 (Stripe 연동)
- **👥 사용자/권한**: 계층형 RBAC 권한 시스템, 2FA 인증
- **🏗️ 현장(Project) 관리**: 개발 현장 통합 관리, 공정률 추적
- **📝 계약(Contract) 관리**: 전자서명, 녹취/녹화 지원
- **💰 회계/수지(Finance)**: 실시간 수지표, 회계 전표 자동 반영
- **🌍 토지(Land) 관리**: 토지 정보, 계약, 동의서 관리
- **🔨 공정(Construction) 추적**: 공정 스케줄, 진행률 관리
- **💎 리츠/투자자(REITs)**: NFT 분양권, DAO 투표, ROI 대시보드
- **🤖 AI 기능**: 상담사 추천, 계약전환율 예측, 공정이상탐지

## 🛠️ 기술 스택

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: Zustand
- **Data Fetching**: React Query (TanStack Query)

### Backend
- **Framework**: NestJS
- **Language**: TypeScript
- **ORM**: Prisma
- **Database**: PostgreSQL
- **Cache**: Redis
- **Authentication**: JWT + Passport
- **Authorization**: CASL (RBAC)

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Monitoring**: Prometheus + Grafana + Loki
- **Cloud**: AWS (ECS, RDS, S3, CloudFront)

### Integrations
- **Payment**: Stripe / TossPayments
- **AI**: OpenAI GPT-4
- **Storage**: AWS S3
- **Web3**: NFT (Fractional), DAO Governance

## 📁 프로젝트 구조

```
satongpaltang/
├── apps/
│   ├── backend/          # NestJS API
│   │   ├── src/
│   │   │   ├── auth/     # 인증 모듈
│   │   │   ├── tenant/   # 테넌트 관리
│   │   │   ├── user/     # 사용자 관리
│   │   │   ├── project/  # 현장 관리
│   │   │   ├── contract/ # 계약 관리
│   │   │   ├── finance/  # 회계/수지
│   │   │   ├── land/     # 토지 관리
│   │   │   ├── construction/ # 공정 관리
│   │   │   ├── investor/ # 투자자/NFT
│   │   │   ├── ai/       # AI 서비스
│   │   │   └── billing/  # 결제 관리
│   │   └── package.json
│   └── frontend/         # Next.js 앱
│       ├── src/
│       │   ├── app/      # 페이지 (App Router)
│       │   ├── components/ # 컴포넌트
│       │   └── lib/      # 유틸리티
│       └── package.json
├── packages/
│   ├── database/         # Prisma 스키마
│   │   ├── prisma/
│   │   │   └── schema.prisma
│   │   └── index.ts
│   ├── shared/           # 공통 타입/유틸
│   └── ui/               # 공통 UI 컴포넌트
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── prometheus/
│   ├── grafana/
│   └── loki/
├── docker-compose.yml
├── package.json
├── turbo.json
└── README.md
```

## 🚀 시작하기

### 사전 요구사항

- Node.js 18+
- npm 9+
- Docker & Docker Compose (선택사항)
- PostgreSQL 15+ (Docker 사용 시 불필요)

### 1. 의존성 설치

```bash
npm install
```

### 2. 환경 변수 설정

루트 디렉토리에 `.env` 파일 생성:

```bash
cp .env.example .env
```

환경 변수를 적절히 수정하세요:

```env
DATABASE_URL="postgresql://user:password@localhost:5432/satongpaltang?schema=public"
JWT_SECRET="your-secret-key"
STRIPE_SECRET_KEY="sk_test_..."
OPENAI_API_KEY="sk-..."
NEXT_PUBLIC_API_BASE="http://localhost:3001/api"
```

### 3. 데이터베이스 마이그레이션

```bash
cd packages/database
npx prisma migrate dev
npx prisma generate
```

### 4. 개발 서버 실행

```bash
npm run dev
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:3001
- **API 문서**: http://localhost:3001/api/docs

### 5. Docker로 실행 (프로덕션)

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

서비스 접근:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:3001
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3003 (admin/admin)

## 📚 API 문서

### 주요 엔드포인트

#### 인증
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `POST /api/auth/2fa/enable` - 2FA 활성화
- `POST /api/auth/2fa/verify` - 2FA 인증

#### 테넌트
- `POST /api/tenants` - 테넌트 생성
- `GET /api/tenants` - 테넌트 목록
- `GET /api/tenants/:id` - 테넌트 상세
- `PATCH /api/tenants/:id` - 테넌트 수정

#### 프로젝트 (현장)
- `POST /api/projects` - 프로젝트 생성
- `GET /api/projects` - 프로젝트 목록
- `GET /api/projects/:id` - 프로젝트 상세
- `PATCH /api/projects/:id` - 프로젝트 수정

#### 계약
- `POST /api/contracts` - 계약 생성
- `GET /api/contracts` - 계약 목록
- `GET /api/contracts/:id` - 계약 상세
- `PATCH /api/contracts/:id/status` - 계약 상태 변경

#### 회계/수지
- `POST /api/finance/ledger` - 회계 전표 생성
- `GET /api/finance/ledger` - 전표 목록
- `POST /api/finance/budget` - 예산 생성
- `GET /api/finance/budget` - 예산 목록
- `GET /api/finance/cashflow` - 현금흐름 조회

#### AI
- `POST /api/ai/recommend-salesperson` - 상담사 추천
- `POST /api/ai/forecast-conversion` - 계약전환율 예측
- `POST /api/ai/analyze-construction` - 공정 분석

#### 결제
- `POST /api/billing/create-checkout` - 결제 세션 생성
- `POST /api/billing/webhook` - Stripe 웹훅
- `GET /api/billing/subscription` - 구독 정보 조회

자세한 API 문서는 http://localhost:3001/api/docs 에서 확인하세요.

## 🔐 권한 시스템 (RBAC)

### 역할 계층

```
0  - SYSTEM_ADMIN      (시스템 관리자)
10 - TENANT_ADMIN      (사업자 관리자)
20 - CM                (건설관리자)
30 - PM                (프로젝트 관리자)
40 - DIRECTOR          (본부장)
50 - MANAGER           (팀장)
60 - SALESPERSON       (상담사)
70 - CUSTOMER          (고객)
```

상위 직급은 하위 직급의 모든 권한을 상속받습니다.

## 🗃️ 데이터베이스 스키마

### 주요 모델

- **Tenant**: 테넌트 (사업자)
- **User**: 사용자
- **Role**: 역할
- **Project**: 프로젝트 (현장)
- **Contract**: 계약
- **Ledger**: 회계 원장
- **FinanceBudget**: 수지표
- **Land**: 토지 정보
- **Construction**: 공정 정보
- **Investor**: 투자자
- **NFT**: NFT 토큰
- **AuditLog**: 감사 로그

모든 모델은 `tenantId`를 포함하여 멀티테넌트를 지원합니다.

## 📊 모니터링

### Prometheus

메트릭 수집 및 알림:
- API 응답 시간
- 데이터베이스 쿼리 성능
- 시스템 리소스 사용량

### Grafana

시각화 대시보드:
- 실시간 트래픽 모니터링
- 오류율 추적
- 사용자 활동 분석

### Loki

로그 수집 및 분석:
- 애플리케이션 로그
- 에러 로그
- 감사 로그

## 🧪 테스트

```bash
# 유닛 테스트
npm run test

# E2E 테스트
npm run test:e2e

# 커버리지
npm run test:cov
```

## 📦 빌드 & 배포

### 로컬 빌드

```bash
npm run build
```

### Docker 이미지 빌드

```bash
# Backend
docker build -f docker/Dockerfile.backend -t satongpaltang-backend .

# Frontend
docker build -f docker/Dockerfile.frontend -t satongpaltang-frontend .
```

### AWS ECS 배포

1. ECR에 이미지 푸시
2. ECS 태스크 정의 업데이트
3. ECS 서비스 업데이트

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

MIT License

## 📞 연락처

프로젝트 링크: [https://github.com/yourusername/satongpaltang](https://github.com/yourusername/satongpaltang)

---

**사통팔땅** - 부동산 개발의 모든 것을 하나의 플랫폼에서