# REQ — 개발 환경

> 이 파일은 Developer가 구현 완료 후 **실제 동작하는 명령어**로 업데이트합니다.

## 기술 스택

- **언어**: (Gate 1에서 확정)
- **프레임워크**: (Gate 1에서 확정)
- **데이터베이스**: (Gate 1에서 확정)
- **패키지 매니저**: (Gate 1에서 확정)

## 설치

```bash
# 의존성 설치
# (구현 후 실제 명령어로 교체)
```

## 실행

```bash
# 개발 서버 실행
# (구현 후 실제 명령어로 교체)
```

## 테스트

```bash
# 단위 테스트 실행
# (구현 후 실제 명령어로 교체)

# 전체 테스트
# (구현 후 실제 명령어로 교체)
```

## 빌드

```bash
# 프로덕션 빌드
# (구현 후 실제 명령어로 교체)
```

## 환경 변수

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS | Agent Teams 모드 활성화 (실험적) | 미설정 | 아니오 |
| (구현 후 작성) | | | |

## Gate 관리 명령어

```bash
# 현재 Gate 정합성 검사
python vulcan.py check-trace

# Gate 상태 업데이트
python vulcan.py session --gate gate1 --status done --feature "기능명"

# 스냅샷 생성
python vulcan.py export
```
