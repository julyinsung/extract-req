from pydantic import BaseModel


class OriginalRequirement(BaseModel):
    """HWP 파싱으로 추출된 원본 요구사항 1건."""

    id: str                # 예: "REQ-001"  (HWP 원문 ID 그대로)
    category: str          # 요구사항 분류  (예: "기능요구사항")
    name: str              # 요구사항 명칭
    content: str           # 요구사항 내용
    order_index: int       # 화면/엑셀 출력 순서 (0-based)


class DetailRequirement(BaseModel):
    """AI 생성 상세요구사항 1건.

    id 채번 규칙: {parent_id}-{NN} 형식 (예: REQ-001-01).
    AI 응답에 ID가 누락되거나 형식이 맞지 않으면 서버에서 재생성한다.
    """

    id: str                      # 예: "REQ-001-01"
    parent_id: str               # 예: "REQ-001"  (OriginalRequirement.id 참조)
    category: str                # 분류 (원본과 동일하거나 세분화 가능)
    name: str                    # 상세 요구사항 명칭
    content: str                 # 상세 요구사항 내용
    order_index: int             # 동일 parent 내 순서 (0-based)
    is_modified: bool = False    # 채팅/인라인편집으로 수정된 경우 True (UI 강조용, REQ-004-02)
