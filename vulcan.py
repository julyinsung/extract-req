#!/usr/bin/env python3
"""
Vulcan-Claude - 5-Gate AI 협업 개발 프레임워크 (Claude Code 네이티브 하네스)

대장장이 신 Vulcan처럼, 에이전트 팀을 단련하여 체계적으로 프로젝트를 완성합니다.
Agent-Forge의 5-Gate 프로세스를 Claude Code 네이티브 하네스(.claude/) 구조로 재구현.

명령어:
  init         새 프로젝트 초기화
  session      Gate 상태 업데이트 + git commit 자동 생성
  check-trace  Gate별 정합성 검사
  export       snapshot.json 생성 (대시보드용)
  upgrade      프레임워크 파일을 최신 버전으로 업데이트
  version      현재 프레임워크 버전 확인

사용법:
  # 초기화 (Vulcan-Claude 디렉토리에서 실행)
  python vulcan.py init <target-dir> <project-name> [--agent-name NAME]

  # 이하 명령은 프로젝트 디렉토리에서 실행
  python vulcan.py check-trace
  python vulcan.py session --gate gate1 --status done --feature "로그인 기능"
  python vulcan.py export [--output snapshot.json]
  python vulcan.py upgrade
"""

import argparse
import io
import json
import os
import re
import subprocess
import sys
from datetime import date

# Windows 콘솔 UTF-8 출력 보장
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

VULCAN_VERSION = "1.0.0"

VULCAN_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(VULCAN_DIR, "templates")

GATE_LABELS = {
    "gate1": "Gate 1 요구사항",
    "gate2": "Gate 2 설계",
    "gate3": "Gate 3 테스트 플랜",
    "impl":  "구현",
    "gate4": "Gate 4 QA 검토",
    "gate5": "Gate 5 최종 승인",
}


# ── 공통 유틸 ──────────────────────────────────────────────────────────────

def render(text, variables):
    for key, value in variables.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def read_template(rel_path):
    path = os.path.join(TEMPLATES_DIR, rel_path)
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_file(target_dir, rel_path, content):
    full_path = os.path.join(target_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  생성: {rel_path}")


def copy_file(target_dir, rel_path, src_rel_path=None):
    import shutil
    src = os.path.join(TEMPLATES_DIR, src_rel_path or rel_path)
    dst = os.path.join(target_dir, rel_path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  생성: {rel_path}")


def copy_tree(src_dir, dst_dir):
    """디렉토리 트리를 재귀적으로 복사합니다."""
    import shutil
    for root, dirs, files in os.walk(src_dir):
        rel_root = os.path.relpath(root, src_dir)
        for f in files:
            src = os.path.join(root, f)
            rel_path = os.path.join(rel_root, f) if rel_root != "." else f
            dst = os.path.join(dst_dir, rel_path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


def load_session(project_dir="."):
    path = os.path.join(project_dir, "session.json")
    if not os.path.exists(path):
        print("오류: session.json을 찾을 수 없습니다. 프로젝트 디렉토리에서 실행하세요.")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_session(session, project_dir="."):
    path = os.path.join(project_dir, "session.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)


def git_commit(message, project_dir=".", include_source=False):
    try:
        subprocess.run(["git", "add", "session.json"], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(["git", "add", "docs/"], cwd=project_dir, check=True, capture_output=True)
        if include_source:
            # 구현/QA 이후: .gitignore가 관리하는 범위 내에서 모든 변경 포함
            subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], cwd=project_dir, check=True, capture_output=True)
        print(f"  커밋 완료: {message}")
    except subprocess.CalledProcessError as e:
        print(f"  경고: git commit 실패 - {e.stderr.decode().strip()}")


# ── check-trace ────────────────────────────────────────────────────────────

def parse_requirements(project_dir="."):
    """REQUIREMENTS.md에서 REQ-ID 및 AC 정보를 파싱합니다."""
    path = os.path.join(project_dir, "docs", "01-requirements", "REQUIREMENTS.md")
    if not os.path.exists(path):
        return set(), set(), set()

    with open(path, encoding="utf-8") as f:
        content = f.read()

    detail_reqs = set(re.findall(r'\bREQ-\d{3}-\d{2}\b', content))
    all_reqs = set(re.findall(r'\bREQ-\d{3}\b', content))
    group_reqs = {r for r in all_reqs if not re.match(r'REQ-\d{3}-\d{2}', r)}
    defined_acs = set(re.findall(r'###\s+AC-(\d{3}-\d{2})', content))

    # AC 위임 관계 파싱: REQ-XXX-XX 행에 자기 AC는 없지만 다른 AC-ID가 참조되면 위임
    ac_delegates = {}
    for line in content.splitlines():
        m_req = re.search(r'\bREQ-(\d{3}-\d{2})\b', line)
        if m_req:
            req_id = m_req.group(1)
            if req_id not in defined_acs:
                refs = re.findall(r'\bAC-(\d{3}-\d{2})\b', line)
                for ref in refs:
                    if ref != req_id:
                        ac_delegates[req_id] = ref
                        break

    return group_reqs, detail_reqs, defined_acs, ac_delegates


def parse_test_plan(project_dir="."):
    """TEST_PLAN.md에서 TST-ID → REQ-ID 매핑을 파싱합니다."""
    path = os.path.join(project_dir, "docs", "03-test-plan", "TEST_PLAN.md")
    if not os.path.exists(path):
        return set()

    with open(path, encoding="utf-8") as f:
        content = f.read()

    return set(re.findall(r'\bREQ-\d{3}-\d{2}\b', content))


def parse_test_plan_status(project_dir="."):
    """TEST_PLAN.md에서 TST-ID별 실행 상태를 파싱합니다.
    마크다운 테이블 행에서 '| TST-NNN-NN |' 패턴만 파싱합니다.
    템플릿 행(TST-ID, TST-NNN-NN 등)과 본문 참조는 무시합니다.
    Returns: list of (tst_id, status) tuples
    """
    path = os.path.join(project_dir, "docs", "03-test-plan", "TEST_PLAN.md")
    if not os.path.exists(path):
        return []

    with open(path, encoding="utf-8") as f:
        content = f.read()

    results = []
    for line in content.splitlines():
        # 마크다운 테이블 행만 대상 (|로 시작)
        if not line.strip().startswith('|'):
            continue
        # 구체적인 TST-ID만 매칭 (TST-NNN-NN 또는 TST-SEC-NN 형식)
        # TST-ID, TST-NNN-NN 같은 템플릿/플레이스홀더는 제외
        tst_match = re.search(r'\|\s*(TST-(?:\d{3}-\d{2}|SEC-\d{2}))\s*\|', line)
        if not tst_match:
            continue
        tst_id = tst_match.group(1)

        # 상태 판별: Pass/Fail/Skip/미실행
        line_lower = line.lower()
        if re.search(r'\bpass\b', line_lower):
            status = 'pass'
        elif re.search(r'\bfail\b', line_lower):
            status = 'fail'
        elif re.search(r'\bskip\b', line_lower):
            status = 'skip'
        else:
            status = 'not_executed'

        results.append((tst_id, status))

    return results


def check_trace(project_dir="."):
    session = load_session(project_dir)
    current_gate = session.get("current_gate", "gate1")
    issues = []

    print(f"\n[check-trace] {session.get('project', '프로젝트')} - {GATE_LABELS.get(current_gate, current_gate)}\n")

    group_reqs, detail_reqs, defined_acs, ac_delegates = parse_requirements(project_dir)

    # ── Gate 1: REQ-ID별 AC 존재 여부
    if current_gate == "gate1":
        print("  Gate 1 검사: 인수 기준(AC) 정의 여부")
        if not detail_reqs:
            issues.append("REQUIREMENTS.md에 REQ-NNN-NN 형식의 요구사항이 없습니다.")
        for req in sorted(detail_reqs):
            ac_id = req.replace("REQ-", "")
            if ac_id in defined_acs:
                print(f"  O {req} - AC 확인")
            elif ac_id in ac_delegates and ac_delegates[ac_id] in defined_acs:
                print(f"  O {req} - AC-{ac_delegates[ac_id]} 위임 확인")
            else:
                issues.append(f"  X {req} - AC 미정의")

    # ── Gate 2: REQ 그룹별 설계 파일 존재 여부
    if current_gate == "gate2":
        print("  Gate 2 검사: REQ 그룹별 설계 파일 존재 여부")
        design_dir = os.path.join(project_dir, "docs", "02-design")
        for group in sorted(group_reqs):
            filename = f"{group.lower()}-design.md"
            filepath = os.path.join(design_dir, filename)
            if os.path.exists(filepath):
                print(f"  O {group} - {filename} 확인")
            else:
                issues.append(f"  X {group} - docs/02-design/{filename} 없음")

    # ── Gate 3: 모든 REQ-NNN-NN에 TST-ID 매핑 여부
    if current_gate == "gate3":
        print("  Gate 3 검사: REQ-ID별 TST-ID 커버리지")
        covered = parse_test_plan(project_dir)
        for req in sorted(detail_reqs):
            if req in covered:
                print(f"  O {req} - TST 매핑 확인")
            else:
                issues.append(f"  X {req} - TEST_PLAN.md에 TST 매핑 없음")

    # ── Gate 4: REQ 그룹별 리뷰 파일 + TST-ID 실행 상태
    if current_gate == "gate4":
        print("  Gate 4 검사 (1): REQ 그룹별 리뷰 파일 존재 여부")
        review_dir = os.path.join(project_dir, "docs", "04-review")
        for group in sorted(group_reqs):
            filename = f"{group.lower()}-review.md"
            filepath = os.path.join(review_dir, filename)
            if os.path.exists(filepath):
                print(f"  O {group} - {filename} 확인")
            else:
                issues.append(f"  X {group} - docs/04-review/{filename} 없음")

        print("\n  Gate 4 검사 (2): TST-ID 실행 상태")
        tst_results = parse_test_plan_status(project_dir)
        if not tst_results:
            issues.append("TEST_PLAN.md에 TST-ID가 없거나 파일이 존재하지 않습니다.")
        else:
            not_executed = [(tid, s) for tid, s in tst_results if s == 'not_executed']
            failed = [(tid, s) for tid, s in tst_results if s == 'fail']
            passed = [(tid, s) for tid, s in tst_results if s == 'pass']
            skipped = [(tid, s) for tid, s in tst_results if s == 'skip']

            print(f"  총 {len(tst_results)}건: Pass {len(passed)}, Fail {len(failed)}, Skip {len(skipped)}, 미실행 {len(not_executed)}")

            for tid, _ in passed:
                print(f"  O {tid} - Pass")
            for tid, _ in skipped:
                print(f"  - {tid} - Skip")
            for tid, _ in failed:
                issues.append(f"  X {tid} - Fail")
                print(f"  X {tid} - Fail")
            for tid, _ in not_executed:
                issues.append(f"  X {tid} - 미실행")
                print(f"  X {tid} - 미실행")

    print()
    if issues:
        print(f"이슈 {len(issues)}건 발견 - Gate 완료 불가:\n")
        for issue in issues:
            print(f"  {issue}")
        sys.exit(1)
    else:
        print("이슈 0건 - Gate 완료 가능합니다.")


# ── session ────────────────────────────────────────────────────────────────

def cmd_session(gate, status, feature, project_dir="."):
    session = load_session(project_dir)

    if gate not in GATE_LABELS:
        print(f"오류: 유효하지 않은 gate - {gate}")
        print(f"  사용 가능: {', '.join(GATE_LABELS.keys())}")
        sys.exit(1)

    if feature:
        session["feature"] = feature

    session["gate_status"][gate] = status

    gate_order = ["gate1", "gate2", "gate3", "impl", "gate4", "gate5"]
    if status == "done":
        current_idx = gate_order.index(gate)
        if current_idx + 1 < len(gate_order):
            session["current_gate"] = gate_order[current_idx + 1]
        else:
            session["current_gate"] = "completed"

        entry = f"{GATE_LABELS[gate]} - {session.get('feature', '')}"
        if entry not in session.get("completed", []):
            session.setdefault("completed", []).append(entry)

    save_session(session, project_dir)
    print(f"  session.json 업데이트: {gate} → {status}")

    feature_label = session.get("feature", "")
    commit_msg = f"session: {gate} done - {GATE_LABELS[gate]}"
    if feature_label:
        commit_msg += f" ({feature_label})"
    # 구현(impl), Gate 4(QA리뷰), Gate 5(최종승인): 소스코드 포함 커밋
    include_source = gate in ("impl", "gate4", "gate5")
    git_commit(commit_msg, project_dir, include_source=include_source)


# ── export ────────────────────────────────────────────────────────────────

def git_log_timeline(project_dir="."):
    try:
        result = subprocess.run(
            ["git", "log", "--grep=^session:", "--date=short",
             "--pretty=format:%H|%ad|%s", "--", "session.json"],
            cwd=project_dir, capture_output=True, text=True, check=True
        )
        timeline = []
        for line in result.stdout.strip().splitlines():
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue
            commit, date_str, message = parts
            timeline.append({"commit": commit[:7], "date": date_str, "message": message})
        return list(reversed(timeline))
    except subprocess.CalledProcessError:
        return []


def collect_documents(project_dir="."):
    docs = {"requirements": None, "design": [], "test_plan": None, "review": []}

    req = os.path.join(project_dir, "docs", "01-requirements", "REQUIREMENTS.md")
    if os.path.exists(req):
        docs["requirements"] = "docs/01-requirements/REQUIREMENTS.md"

    design_dir = os.path.join(project_dir, "docs", "02-design")
    if os.path.isdir(design_dir):
        docs["design"] = sorted([
            f"docs/02-design/{f}" for f in os.listdir(design_dir) if f.endswith(".md")
        ])

    tp = os.path.join(project_dir, "docs", "03-test-plan", "TEST_PLAN.md")
    if os.path.exists(tp):
        docs["test_plan"] = "docs/03-test-plan/TEST_PLAN.md"

    review_dir = os.path.join(project_dir, "docs", "04-review")
    if os.path.isdir(review_dir):
        docs["review"] = sorted([
            f"docs/04-review/{f}" for f in os.listdir(review_dir) if f.endswith(".md")
        ])

    return docs


def cmd_export(output="snapshot.json", project_dir="."):
    from datetime import datetime
    session = load_session(project_dir)

    snapshot = {
        "schema_version": "1.0",
        "framework": "vulcan-claude",
        "project": session.get("project", ""),
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "current_gate": session.get("current_gate", "gate1"),
        "gate_status": session.get("gate_status", {}),
        "feature": session.get("feature", ""),
        "started": session.get("started", ""),
        "completed": session.get("completed", []),
        "blocked": session.get("blocked", []),
        "timeline": git_log_timeline(project_dir),
        "documents": collect_documents(project_dir),
    }

    out_path = os.path.join(project_dir, output)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    print(f"  snapshot 생성: {output}")
    print(f"  프로젝트: {snapshot['project']} | Gate: {snapshot['current_gate']}")


# ── upgrade ────────────────────────────────────────────────────────────────

FRAMEWORK_FILES = [
    ".claude/CLAUDE.md",
    ".claude/agents/pm.md",
    ".claude/agents/architect.md",
    ".claude/agents/dba.md",
    ".claude/agents/frontend-dev.md",
    ".claude/agents/backend-dev.md",
    ".claude/agents/qa.md",
    ".claude/skills/vulcan/skill.md",
    ".claude/skills/gate-transition/skill.md",
    ".claude/skills/security-baseline/skill.md",
    "commenting-standards.md",
    "GATE_GUIDE.md",
    "docs/05-security/baseline.md",
]


def read_version_from_vulcan(vulcan_py_path):
    try:
        with open(vulcan_py_path, encoding="utf-8") as f:
            content = f.read()
        match = re.search(r'^VULCAN_VERSION\s*=\s*["\'](.+?)["\']', content, re.MULTILINE)
        return match.group(1) if match else "unknown"
    except OSError:
        return "unknown"


def extract_variables(project_dir="."):
    """CLAUDE.md에서 프로젝트 변수 추출."""
    claude_path = os.path.join(project_dir, ".claude", "CLAUDE.md")
    if not os.path.exists(claude_path):
        print("오류: .claude/CLAUDE.md를 찾을 수 없습니다.")
        sys.exit(1)

    with open(claude_path, encoding="utf-8") as f:
        content = f.read()

    project = re.search(r'^# (.+?)(?:\s+-|\s+Harness)', content, re.MULTILINE)
    generated = re.search(r'생성일: (.+)', content)

    session = load_session(project_dir)

    return {
        "PROJECT_NAME": project.group(1).strip() if project else session.get("project", "Unknown"),
        "GENERATED_DATE": generated.group(1).strip() if generated else str(date.today()),
    }


def cmd_upgrade(project_dir="."):
    import shutil

    session = load_session(project_dir)
    vulcan_src = session.get("vulcan_src", "")
    src_templates = os.path.join(vulcan_src, "templates") if vulcan_src else ""

    if not vulcan_src or not os.path.isdir(src_templates):
        print("오류: Vulcan-Claude 원본 경로를 찾을 수 없습니다.")
        print("  session.json의 'vulcan_src' 경로를 확인하세요.")
        sys.exit(1)

    current_ver = session.get("vulcan_version", "unknown")
    src_vulcan = os.path.join(vulcan_src, "vulcan.py")
    new_ver = read_version_from_vulcan(src_vulcan)

    variables = extract_variables(project_dir)
    print(f"\nVulcan-Claude upgrade")
    print(f"  프로젝트: {variables['PROJECT_NAME']}")
    print(f"  버전: {current_ver} → {new_ver}")
    print(f"  소스: {vulcan_src}\n")

    for rel_path in FRAMEWORK_FILES:
        tpl_path = os.path.join(src_templates, rel_path)
        if not os.path.exists(tpl_path):
            print(f"  건너뜀 (템플릿 없음): {rel_path}")
            continue
        with open(tpl_path, encoding="utf-8") as f:
            content = render(f.read(), variables)
        dst = os.path.join(project_dir, rel_path)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  업데이트: {rel_path}")

    if os.path.exists(src_vulcan):
        shutil.copy2(src_vulcan, os.path.join(project_dir, "vulcan.py"))
        print(f"  업데이트: vulcan.py")

    session["vulcan_version"] = new_ver
    save_session(session, project_dir)

    print(f"\n완료! v{current_ver} → v{new_ver}")
    print(f"보존된 파일: ENVIRONMENT.md, session.json, docs/")


# ── version ───────────────────────────────────────────────────────────────

def cmd_version(project_dir="."):
    print(f"Vulcan-Claude v{VULCAN_VERSION}")
    session_path = os.path.join(project_dir, "session.json")
    if os.path.exists(session_path):
        session = load_session(project_dir)
        project_ver = session.get("vulcan_version", "unknown")
        print(f"  프로젝트: {session.get('project', '-')} (설치 버전: {project_ver})")


# ── init ───────────────────────────────────────────────────────────────────

def create_session_json(target_dir, project_name):
    session = {
        "project": project_name,
        "vulcan_src": VULCAN_DIR,
        "vulcan_version": VULCAN_VERSION,
        "current_gate": "gate1",
        "gate_status": {
            "gate1": "pending",
            "gate2": "pending",
            "gate3": "pending",
            "impl":  "pending",
            "gate4": "pending",
            "gate5": "pending"
        },
        "feature": "",
        "started": str(date.today()),
        "completed": [],
        "pending": [],
        "blocked": []
    }
    write_file(target_dir, "session.json", json.dumps(session, ensure_ascii=False, indent=2))


def init(target_dir, project_name, agent_name):
    import shutil
    print(f"\nVulcan-Claude 초기화")
    print(f"  프로젝트: {project_name}")
    print(f"  대상 폴더: {target_dir}\n")

    if os.path.exists(target_dir):
        files = os.listdir(target_dir)
        if files:
            print(f"경고: {target_dir} 폴더가 비어있지 않습니다.")
            answer = input("계속 진행할까요? (y/N): ").strip().lower()
            if answer != "y":
                print("취소됨.")
                sys.exit(0)
    else:
        os.makedirs(target_dir)

    variables = {
        "PROJECT_NAME": project_name,
        "GENERATED_DATE": str(date.today()),
    }

    # .claude/ 디렉토리 전체 복사 후 변수 치환
    src_claude = os.path.join(TEMPLATES_DIR, ".claude")
    dst_claude = os.path.join(target_dir, ".claude")
    copy_tree(src_claude, dst_claude)
    print(f"  생성: .claude/ (agents 5, skills 3)")

    # .claude/ 내 모든 .md 파일에 변수 치환 적용
    for root, dirs, files in os.walk(dst_claude):
        for f in files:
            if f.endswith(".md"):
                fpath = os.path.join(root, f)
                with open(fpath, encoding="utf-8") as fp:
                    content = render(fp.read(), variables)
                with open(fpath, "w", encoding="utf-8") as fp:
                    fp.write(content)

    # ENVIRONMENT.md
    content = render(read_template("ENVIRONMENT.md"), variables)
    write_file(target_dir, "ENVIRONMENT.md", content)

    # commenting-standards.md
    copy_file(target_dir, "commenting-standards.md")

    # GATE_GUIDE.md
    copy_file(target_dir, "GATE_GUIDE.md")

    # docs/
    content = render(read_template("docs/01-requirements/REQUIREMENTS.md"), variables)
    write_file(target_dir, "docs/01-requirements/REQUIREMENTS.md", content)

    write_file(target_dir, "docs/02-design/.gitkeep", "")

    content = render(read_template("docs/03-test-plan/TEST_PLAN.md"), variables)
    write_file(target_dir, "docs/03-test-plan/TEST_PLAN.md", content)

    write_file(target_dir, "docs/04-review/.gitkeep", "")

    # security
    copy_file(target_dir, "docs/05-security/baseline.md", "docs/05-security/baseline.md")
    write_file(target_dir, "docs/05-security/compliance/.gitkeep", "")

    # session.json
    create_session_json(target_dir, project_name)

    # vulcan.py 자신을 프로젝트에 복사
    shutil.copy2(__file__, os.path.join(target_dir, "vulcan.py"))
    print(f"  생성: vulcan.py")

    # .gitignore
    gitignore = "node_modules/\n.env\n.env.local\ndashboard/.next/\ndashboard/node_modules/\n"
    write_file(target_dir, ".gitignore", gitignore)

    # dashboard/ 복사 (Anvil 대시보드)
    src_dashboard = os.path.join(TEMPLATES_DIR, "dashboard")
    if os.path.isdir(src_dashboard):
        dst_dashboard = os.path.join(target_dir, "dashboard")
        copy_tree(src_dashboard, dst_dashboard)
        print(f"  생성: dashboard/ (Anvil 대시보드 — Next.js)")

    # git init + 초기 커밋
    try:
        subprocess.run(["git", "init"], cwd=target_dir, check=True, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=target_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"init: {project_name} 프로젝트 초기화"],
            cwd=target_dir, check=True, capture_output=True
        )
        print(f"  생성: git 저장소 초기화 + 초기 커밋")
    except Exception as e:
        print(f"  경고: git 초기화 실패 - {e}")

    print(f"\n완료! {project_name} 프로젝트가 초기화되었습니다.")
    print(f"\n다음 단계:")
    print(f"  1. cd {target_dir}")
    print(f"  2. Claude Code 실행")
    print(f"  3. /vulcan 또는 'Gate 1 시작해줘'로 프로세스 시작")
    print(f"\n대시보드 실행:")
    print(f"  cd dashboard && npm install && npm run dev")
    print(f"  브라우저: http://localhost:3001")
    print(f"\nGate 완료 시:")
    print(f"  python vulcan.py check-trace")
    print(f"  python vulcan.py session --gate gate1 --status done --feature '기능명'")


# ── main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Vulcan-Claude - 5-Gate AI 협업 개발 프레임워크",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
명령어:
  init         새 프로젝트 초기화 (Vulcan-Claude 디렉토리에서 실행)
  check-trace  현재 Gate 정합성 검사 (프로젝트 디렉토리에서 실행)
  session      Gate 상태 업데이트 + git commit (프로젝트 디렉토리에서 실행)
  export       snapshot.json 생성 (프로젝트 디렉토리에서 실행)
  upgrade      프레임워크 파일 최신화 (프로젝트 디렉토리에서 실행)
  version      현재 프레임워크 버전 확인

예시:
  python vulcan.py init ../my-app "MyApp"
  python vulcan.py check-trace
  python vulcan.py session --gate gate1 --status done --feature "로그인 기능"
  python vulcan.py export
  python vulcan.py upgrade
        """
    )
    subparsers = parser.add_subparsers(dest="command")

    p_init = subparsers.add_parser("init", help="새 프로젝트 초기화")
    p_init.add_argument("target_dir", help="초기화할 프로젝트 폴더 경로")
    p_init.add_argument("project_name", help="프로젝트 이름")
    p_init.add_argument("--agent-name", default="VULCAN", help="메인 에이전트 이름 (기본값: VULCAN)")

    subparsers.add_parser("check-trace", help="현재 Gate 정합성 검사")

    p_session = subparsers.add_parser("session", help="Gate 상태 업데이트 + git commit")
    p_session.add_argument("--gate", required=True, choices=list(GATE_LABELS.keys()), help="Gate 이름")
    p_session.add_argument("--status", required=True, choices=["done", "pending"], help="상태")
    p_session.add_argument("--feature", default="", help="작업 기능명")

    p_export = subparsers.add_parser("export", help="snapshot.json 생성")
    p_export.add_argument("--output", default="snapshot.json", help="출력 파일명")

    subparsers.add_parser("upgrade", help="프레임워크 파일 최신화")
    subparsers.add_parser("version", help="현재 프레임워크 버전 확인")

    args = parser.parse_args()

    if args.command == "init":
        init(
            target_dir=os.path.abspath(args.target_dir),
            project_name=args.project_name,
            agent_name=args.agent_name,
        )
    elif args.command == "check-trace":
        check_trace()
    elif args.command == "session":
        cmd_session(gate=args.gate, status=args.status, feature=args.feature)
    elif args.command == "export":
        cmd_export(output=args.output)
    elif args.command == "upgrade":
        cmd_upgrade()
    elif args.command == "version":
        cmd_version()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
