# AdGuard AI 백엔드

아래 명령은 모두 `src/backend` 폴더에서 실행합니다. 권한 매트릭스·검증 절차는 [docs/백엔드_인증_권한_검증.md](../../docs/백엔드_인증_권한_검증.md)에 있습니다.

## 처음 설정

1. PostgreSQL 17 설치
   - macOS: `brew install postgresql@17` 후 `brew services start postgresql@17`
   - Windows: PostgreSQL 공식 설치 프로그램(17 버전)
2. DB 만들기: `createdb adguard` (Windows는 pgAdmin에서 `adguard` DB 생성)
3. `.env.example`을 복사해 `.env`를 만들고 `DATABASE_URL`을 자기 DB 주소로 바꾸기 (`.env`는 git에 올리지 않음)
4. 마이그레이션 적용: `uv run alembic upgrade head`

## 계정 만들기

- 개발용 테스트 계정: `uv run python -m app.seed_dev`
  - `admin@adguard.local`, `marketing@adguard.local`, `legal@adguard.local` / 비밀번호 `adguard1234`
- 운영용 첫 ADMIN: `uv run python -m app.cli create-admin --email admin@회사.com --name 관리자`
  - 임시 비밀번호를 한 번만 보여 줍니다.

## 서버 실행

```bash
uv run uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs

## 테스트

```bash
uv run pytest tests
```
