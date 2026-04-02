"""상세요구사항 CRUD 라우터.

PATCH /api/v1/detail/{id} — 특정 상세요구사항의 단일 필드를 수정한다 (REQ-008-01).
DELETE /api/v1/detail/{id} — 특정 상세요구사항을 삭제한다 (REQ-012/REQ-013).
경로 파라미터를 권위 있는 식별자로 사용한다 (RESTful 관례, 설계 문서 트레이드오프 참조).
"""

from fastapi import APIRouter, HTTPException

import app.state as state
from app.models.api import ErrorResponse, InlineEditRequest
from app.models.requirement import DetailRequirement

# SEC-008-03: 상세요구사항 value 최대 길이 — 채팅(2000자)보다 넓은 여유 제공
MAX_VALUE_LENGTH = 5000

router = APIRouter(prefix="/api/v1")


@router.patch(
    "/detail/{id}",
    response_model=DetailRequirement,
    responses={404: {"model": ErrorResponse}},
)
def patch_detail(id: str, req: InlineEditRequest) -> DetailRequirement:
    """특정 상세요구사항의 단일 필드를 수정하고 수정된 항목을 반환한다.

    경로 파라미터 id를 식별자로 사용하며, 바디의 field/value만 patch_detail()에 전달한다.
    SEC-008-01: field는 InlineEditRequest.field Literal 검증으로 허용 범위를 제한한다.
    SEC-008-03: value 길이를 MAX_VALUE_LENGTH로 제한하여 과도한 입력을 방어한다.

    Args:
        id: 수정할 DetailRequirement의 id (경로 파라미터)
        req: InlineEditRequest — field와 value를 포함한 수정 요청

    Returns:
        수정된 DetailRequirement 전체 객체

    Raises:
        HTTPException 422: req.field가 허용 범위 외이거나 value 길이 초과 (Pydantic 자동 처리 + 명시적 검증)
        HTTPException 404: 해당 id의 상세요구사항이 존재하지 않는 경우
    """
    if len(req.value) > MAX_VALUE_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                code="VALUE_TOO_LONG",
                message=f"value는 {MAX_VALUE_LENGTH}자를 초과할 수 없습니다.",
            ).model_dump(),
        )

    success = state.patch_detail(id, req.field, req.value)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                code="NOT_FOUND",
                message=f"해당 ID의 상세요구사항을 찾을 수 없습니다: {id}",
            ).model_dump(),
        )

    # patch_detail() 성공 후 state에서 갱신된 항목을 조회하여 반환한다.
    # state.get_detail()이 동일 _lock 패턴을 사용하므로 스레드 안전성이 보장된다.
    updated = next(r for r in state.get_detail() if r.id == id)
    return updated


@router.delete(
    "/detail/{id}",
    responses={404: {"model": ErrorResponse}},
)
def delete_detail(id: str) -> dict:
    """특정 상세요구사항을 삭제하고 삭제된 id를 반환한다 (REQ-012/REQ-013).

    state.delete_detail()이 스냅샷 저장까지 처리하므로 라우터는 결과만 반환한다.
    SEC-012-02: id는 state 내부에서 문자열 동등 비교로만 사용하여 경로 순회 위협 없음.

    Args:
        id: 삭제할 DetailRequirement의 id (경로 파라미터)

    Returns:
        {"deleted_id": id} — 삭제 성공 시

    Raises:
        HTTPException 404: 해당 id의 상세요구사항이 존재하지 않는 경우
    """
    success = state.delete_detail(id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                code="NOT_FOUND",
                message=f"해당 ID의 상세요구사항을 찾을 수 없습니다: {id}",
            ).model_dump(),
        )

    return {"deleted_id": id}
