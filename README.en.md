# Sisyphus Monorepo

Sisyphus 관련 프로젝트들을 포함하는 모노레포입니다.

## 프로젝트

- **[projects/sisyphus-cli](./projects/sisyphus-cli/)** - Natural Language Compiler - 자연어를 코드로 컴파일하는 메인 CLI 애플리케이션

## 개발 환경 설정

### 초기 설정

```bash
git clone https://github.com/code-yeongyu/sisyphus.git
cd sisyphus
uv sync
```

### CLI 실행

```bash
# 방법 1: 프로젝트 디렉토리로 이동 후 실행
cd projects/sisyphus-cli
uv run sisyphus work

# 방법 2: 루트에서 경로 지정
cd projects/sisyphus-cli && uv run sisyphus work
```

### 테스트 실행

```bash
# 루트에서 실행
uv run pytest projects/sisyphus-cli/tests

# 또는 프로젝트 디렉토리에서
cd projects/sisyphus-cli
uv run pytest
```

### 타입 체크

```bash
cd projects/sisyphus-cli
uv run basedpyright
```

### 린팅

```bash
cd projects/sisyphus-cli
uv run ruff check
```

### 포맷팅

```bash
cd projects/sisyphus-cli
uv run ruff format
```

## 워크스페이스 구조

이 저장소는 UV workspace를 사용하여 여러 프로젝트를 관리합니다:

- **루트 `pyproject.toml`**: 워크스페이스 설정 및 공유 dev dependencies
- **`projects/sisyphus-cli/pyproject.toml`**: sisyphus-ai 패키지 설정

각 프로젝트는 독립적으로 빌드 및 배포가 가능합니다.

## 빌드 및 배포

### 패키지 빌드

```bash
uv build projects/sisyphus-cli
```

### PyPI 배포

Release를 생성하면 자동으로 PyPI에 배포됩니다. (GitHub Actions 사용)

## 라이선스

Sustainable Use License 1.0

---

더 자세한 정보는 [projects/sisyphus-cli/README.md](./projects/sisyphus-cli/README.md)를 참조하세요.
