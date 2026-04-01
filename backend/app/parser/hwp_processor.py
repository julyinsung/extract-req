"""HWP 요구사항 파싱 어댑터.

HWPOLEReader와 HwpBodyParser를 조합하여 OriginalRequirement 리스트를 반환한다.
pandas 의존성을 배제하고 순수 Python 객체만 사용한다 (설계 문서 REQ-001).
기존 파서 클래스(hwp_ole_reader.py, hwp_body_parser.py)는 수정하지 않는다.
"""

from typing import List, Dict

from app.parser.hwp_ole_reader import HWPOLEReader
from app.parser.hwp_body_parser import HwpBodyParser
from app.models.requirement import OriginalRequirement

# 요구사항 테이블 헤더 셀의 고유번호 키워드 (공백 제거 후 비교)
_REQ_ID_KEYWORD = "요구사항고유번호"

# 각 필드 매핑에 사용하는 키워드 (공백·줄바꿈 제거 후 비교)
_FIELD_KEYWORDS = {
    "id":       "요구사항고유번호",
    "name":     "요구사항명칭",
    "category": "요구사항분류",
    "content":  "세부내용",
}

# 세부내용 파싱 종료 신호 키워드
_CONTENT_STOP_KEYWORDS = {"산출물", "참고사항", "요구사항고유번호"}


class HwpProcessor:
    """HWP 파일에서 요구사항을 추출하여 OriginalRequirement 리스트로 반환하는 어댑터."""

    def process(self, file_path: str) -> list[OriginalRequirement]:
        """OLE 스트림을 순회하며 요구사항 항목을 추출한다.

        Args:
            file_path: 임시 저장된 HWP 파일 경로

        Returns:
            추출된 OriginalRequirement 목록 (순서 보장)

        Raises:
            ValueError: 유효한 HWP 파일이 아닌 경우 (HWPOLEReader가 발생)
        """
        parser = HwpBodyParser()
        raw_items: List[Dict] = []

        with HWPOLEReader(file_path) as reader:
            streams = reader.get_bodytext_streams()
            for stream in streams:
                data = reader.get_stream_data(stream)
                raw_items.extend(parser.extract_all(data))

        return self._structure(raw_items)

    # ------------------------------------------------------------------
    # 내부 메서드
    # ------------------------------------------------------------------

    def _structure(self, raw: List[Dict]) -> list[OriginalRequirement]:
        """raw 항목 목록에서 요구사항 테이블을 식별하고 OriginalRequirement로 변환한다.

        "요구사항 고유번호" 셀이 포함된 테이블을 요구사항 블록으로 인식한다.
        동일 ID가 연속으로 등장하면(분리된 테이블 블록) 내용을 이어 붙인다.
        """
        requirements: List[OriginalRequirement] = []
        last_req: Dict | None = None

        for item in raw:
            if item["type"] != "table":
                continue

            cells: List[str] = item["data"].get("cells", [])
            # 공백·줄바꿈 제거 후 비교하여 요구사항 헤더 테이블 판별
            if not any(_REQ_ID_KEYWORD in _normalize(c) for c in cells):
                # 직전 요구사항에 이어지는 본문 테이블일 수 있음 — 내용 합산
                if last_req and len(cells) > 2:
                    continuation = "\n".join(cells).strip()
                    if len(continuation) > 10:
                        last_req["content"] += "\n" + continuation
                continue

            parsed = self._parse_requirement_table(cells)
            if not parsed:
                continue

            if last_req and parsed["id"] == last_req["id"]:
                # 동일 ID 테이블이 분리된 경우 내용 병합
                last_req["content"] += "\n" + parsed["content"]
            else:
                requirements.append(parsed)
                last_req = parsed

        return [
            OriginalRequirement(
                id=r["id"],
                category=r["category"],
                name=r["name"],
                content=r["content"],
                order_index=idx,
            )
            for idx, r in enumerate(requirements)
        ]

    def _parse_requirement_table(self, cells: List[str]) -> Dict | None:
        """셀 목록에서 ID·명칭·분류·세부내용을 파싱한다.

        각 헤더 키워드 다음 셀을 해당 필드 값으로 사용한다.
        세부내용은 키워드 이후 종료 키워드 직전까지의 셀을 이어 붙인다.

        Returns:
            {"id", "name", "category", "content"} 딕셔너리.
            고유번호가 없으면 None 반환.
        """
        req = {"id": "", "name": "", "category": "", "content": ""}
        skip_to = -1

        for i, cell in enumerate(cells):
            if i <= skip_to:
                continue

            norm = _normalize(cell)

            if _FIELD_KEYWORDS["id"] in norm and i + 1 < len(cells):
                req["id"] = cells[i + 1].strip()
                skip_to = i + 1

            elif _FIELD_KEYWORDS["name"] in norm and i + 1 < len(cells):
                req["name"] = cells[i + 1].strip()
                skip_to = i + 1

            elif _FIELD_KEYWORDS["category"] in norm and i + 1 < len(cells):
                req["category"] = cells[i + 1].strip()
                skip_to = i + 1

            elif _FIELD_KEYWORDS["content"] in norm:
                req["content"] = self._collect_content(cells, i + 1, req)
                # 세부내용 이후는 모두 소비했으므로 루프 종료
                break

        if not req["id"]:
            return None
        return req

    def _collect_content(self, cells: List[str], start: int, req: Dict) -> str:
        """start 인덱스부터 종료 키워드 직전까지 세부내용 셀을 수집한다.

        중복된 헤더 키워드나 정의 값은 제외하여 노이즈를 제거한다.
        """
        parts: List[str] = []
        for cell in cells[start:]:
            norm = _normalize(cell)
            raw = cell.strip()

            # 종료 신호
            if any(kw in norm for kw in _CONTENT_STOP_KEYWORDS):
                break

            # 노이즈 키워드 제외
            skip_keywords = {"정의", "세부", "내용", "세부내용", "상세설명"}
            if norm in skip_keywords:
                continue

            # 다른 헤더 필드 값과 중복 제외
            if raw in (req["name"], req["category"]):
                continue

            if raw:
                parts.append(raw)

        return "\n".join(parts).strip()


def _normalize(text: str) -> str:
    """공백·줄바꿈을 제거하여 키워드 비교용 정규화 문자열을 반환한다."""
    return text.replace(" ", "").replace("\n", "").replace("\r", "").strip()
