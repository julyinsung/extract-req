---
name: security-baseline
description: "OWASP Top 10 보안 체크리스트 및 보안 평가 기준. architect가 설계 시 보안 고려사항(SEC-ID)을 작성하고, qa가 Gate 4에서 보안 점검(항목 D)을 수행할 때 참조한다. '보안 점검', 'OWASP', '취약점 체크', '보안 설계' 등 보안 관련 요청 시 사용한다. 단, 침투 테스트 수행이나 보안 인증 심사는 이 스킬의 범위가 아니다."
---

# Security Baseline — OWASP Top 10 보안 체크리스트

architect와 qa 에이전트가 보안 설계 및 검증 시 참조하는 보안 기준선.

## 대상 에이전트

- `architect` — Gate 2에서 SEC-ID 작성 시 참조
- `qa` — Gate 4에서 Blocker 항목 D(보안 점검) 수행 시 참조

## OWASP Top 10 체크리스트

### A01: 접근 제어 취약점 (Broken Access Control)
- [ ] 모든 API 엔드포인트에 인증 확인 적용
- [ ] 객체 수준 인가 (자신의 리소스만 접근 가능)
- [ ] 관리자 기능 권한 분리
- [ ] CORS 설정이 허용 도메인만 포함
- [ ] 디렉토리 리스팅 비활성화

### A02: 암호화 실패 (Cryptographic Failures)
- [ ] 비밀번호는 bcrypt/Argon2로 해싱
- [ ] 민감 데이터 전송 시 HTTPS 강제
- [ ] 암호화 키는 환경변수로 관리 (하드코딩 금지)
- [ ] 약한 암호 알고리즘(MD5, SHA1) 미사용

### A03: 인젝션 (Injection)
- [ ] SQL 파라미터 바인딩 (ORM 또는 Prepared Statement)
- [ ] HTML 출력 시 자동 이스케이핑
- [ ] OS 명령 실행 시 shell=False
- [ ] LDAP, XPath 등 쿼리 파라미터화

### A04: 안전하지 않은 설계 (Insecure Design)
- [ ] 비즈니스 로직 남용 방지 (예: 무제한 쿠폰 사용)
- [ ] Rate Limiting 적용 (로그인, API 호출)
- [ ] 실패 시 안전한 기본값 (Fail-Safe)

### A05: 보안 설정 오류 (Security Misconfiguration)
- [ ] 기본 관리자 계정 비활성화
- [ ] 불필요한 HTTP 메서드 차단
- [ ] 스택 트레이스 / 디버그 정보 미노출
- [ ] 보안 헤더 설정 (CSP, X-Frame-Options, HSTS)

### A06: 취약한 컴포넌트 (Vulnerable Components)
- [ ] 의존성에 알려진 CVE 없음
- [ ] 정기적 의존성 업데이트 계획
- [ ] 불필요한 의존성 제거

### A07: 인증 실패 (Authentication Failures)
- [ ] 강력한 비밀번호 정책 (최소 8자, 복잡도)
- [ ] 로그인 실패 횟수 제한 + 계정 잠금
- [ ] 세션 토큰 안전한 생성 (충분한 엔트로피)
- [ ] 로그아웃 시 서버 측 세션 무효화

### A08: 데이터 무결성 실패 (Data Integrity Failures)
- [ ] 외부 데이터 역직렬화 검증
- [ ] CI/CD 파이프라인 무결성 확인
- [ ] 자동 업데이트 서명 검증

### A09: 로깅/모니터링 부족 (Logging Failures)
- [ ] 인증 실패, 접근 제어 실패 로깅
- [ ] 로그에 민감 정보(비밀번호, 토큰) 미포함
- [ ] 로그 변조 방지 (별도 저장소)

### A10: SSRF (Server-Side Request Forgery)
- [ ] 사용자 입력 URL 화이트리스트 검증
- [ ] 내부 네트워크 IP 접근 차단
- [ ] URL 리다이렉트 제한

## SEC-ID 작성 가이드 (Architect용)

설계 문서에 보안 고려사항을 SEC-ID로 식별한다:

| SEC-ID | 위협 | 대응 방안 | OWASP | 심각도 |
|--------|------|----------|-------|--------|
| SEC-001-01 | SQL Injection | ORM 파라미터 바인딩 | A03 | Critical |
| SEC-001-02 | 하드코딩 비밀번호 | 환경변수 분리 | A02 | Critical |
| SEC-001-03 | IDOR | 객체 수준 인가 미들웨어 | A01 | High |

## 보안 점검 가이드 (QA용)

Gate 4 Blocker 항목 D 평가 시:

1. 설계 문서의 SEC-ID 목록을 확인한다
2. 각 SEC-ID의 대응 방안이 코드에 구현되었는지 검증한다
3. `docs/05-security/baseline.md`의 OWASP 체크리스트를 대조한다
4. 프로젝트별 추가 보안 요건은 `docs/05-security/compliance/`를 확인한다

### 판정 기준
- **Pass**: 모든 SEC-ID 대응 완료 + OWASP 체크리스트 Critical/High 항목 충족
- **Fail**: SEC-ID 대응 미구현 1건 이상 또는 Critical 취약점 발견
