import zlib
import struct
from typing import List, Dict

class HwpBodyParser:
    """
    HWP BodyText 스트림의 압축을 해제하고 레코드를 파싱하여 텍스트를 추출하는 클래스.

    REQ-ID: REQ-101-02, REQ-101-03
    """
    
    # HWP 레코드 태그 ID 정의
    HWPTAG_BEGIN = 0x10
    HWPTAG_PARA_HEADER = HWPTAG_BEGIN + 50
    HWPTAG_PARA_TEXT = HWPTAG_BEGIN + 51
    HWPTAG_CTRL_HEADER = HWPTAG_BEGIN + 55
    HWPTAG_LIST_HEADER = HWPTAG_BEGIN + 56
    HWPTAG_TABLE = HWPTAG_BEGIN + 61
    
    def __init__(self):
        pass

    def extract_text(self, stream_data: bytes, compressed: bool = True) -> str:
        """
        스트림 데이터를 받아 압축 해제 후 순수 텍스트를 추출합니다. (기존 호환용)

        Args:
            stream_data: HWP BodyText 스트림의 원시 바이너리 데이터
            compressed: 데이터 압축 여부 (기본값: True)
        Returns:
            줄바꿈으로 구분된 순수 텍스트 문자열
        """
        records = self._get_records(stream_data, compressed)
        return self._extract_para_text(records)

    def extract_all(self, stream_data: bytes, compressed: bool = True) -> List[Dict]:
        """
        텍스트와 표 구조를 포함한 모든 데이터를 추출하여 리스트로 반환합니다.

        Args:
            stream_data: HWP BodyText 스트림의 원시 바이너리 데이터
            compressed: 데이터 압축 여부 (기본값: True)
        Returns:
            각 항목이 {'type': 'text'|'table', 'content'|'data': ...} 형태인 딕셔너리 리스트
        """
        records = self._get_records(stream_data, compressed)
        
        results = []
        i = 0
        while i < len(records):
            record = records[i]
            
            if record['tag_id'] == self.HWPTAG_TABLE:
                # 표 데이터 처리
                table_data, next_index = self._parse_table(records, i)
                results.append({"type": "table", "data": table_data})
                i = next_index
                continue
            
            if record['tag_id'] == self.HWPTAG_PARA_TEXT:
                text = self._decode_text(record['data'])
                if text:
                    results.append({"type": "text", "content": text})
            
            i += 1
            
        return results

    def _get_records(self, stream_data: bytes, compressed: bool) -> List[Dict]:
        if compressed:
            data = self._decompress(stream_data)
        else:
            data = stream_data
        return self._parse_records(data)

    def _parse_table(self, records: List[Dict], start_index: int) -> (Dict, int):
        """표 레코드에서 행/열 정보를 추출하고 모든 셀 데이터를 수집합니다."""
        table_record = records[start_index]
        
        # 행/열 개수 추출 (HWP 5.0 Spec: Property(4), Row(2), Col(2))
        rows = 0
        cols = 0
        if len(table_record['data']) >= 8:
            rows = struct.unpack('<H', table_record['data'][4:6])[0]
            cols = struct.unpack('<H', table_record['data'][6:8])[0]
            
        all_cells = []
        i = start_index + 1
        while i < len(records):
            record = records[i]
            
            if record['level'] <= table_record['level'] and record['tag_id'] != self.HWPTAG_LIST_HEADER:
                break
                
            if record['tag_id'] == self.HWPTAG_LIST_HEADER:
                cell_text, next_i = self._parse_cell(records, i)
                all_cells.append(cell_text)
                i = next_index = next_i
                continue
            
            i += 1
            
        return {"cells": all_cells, "rows": rows, "cols": cols}, i

    def _parse_cell(self, records: List[Dict], list_header_index: int) -> (str, int):
        """PARA_TEXT를 수집하며 중첩된 표를 마크다운 형식으로 변환합니다."""
        header_record = records[list_header_index]
        cell_lines = []
        
        i = list_header_index + 1
        while i < len(records):
            record = records[i]
            if record['tag_id'] == self.HWPTAG_LIST_HEADER and record['level'] <= header_record['level']:
                break
            if record['level'] < header_record['level']:
                break
                
            if record['tag_id'] == self.HWPTAG_PARA_TEXT:
                text = self._decode_text(record['data'])
                if text:
                    cell_lines.append(text)
            
            elif record['tag_id'] == self.HWPTAG_TABLE:
                nested, next_i = self._parse_table(records, i)
                if nested.get("cells"):
                    # 가독성을 위해 마크다운 표 형식으로 변환
                    md_table = self._format_as_markdown_table(nested["cells"], nested["cols"])
                    cell_lines.append("\n" + md_table + "\n")
                i = next_i
                continue
                
            i += 1
            
        return "\n".join(cell_lines), i

    def _format_as_markdown_table(self, cells: List[str], col_count: int) -> str:
        """셀 리스트를 마크다운 표 문자열로 변환합니다. 내부 줄바꿈은 <br>로 치환합니다."""
        if not col_count or not cells:
            return " | ".join(cells)
            
        rows = []
        # 셀 데이터를 열 개수에 맞춰 분할
        for i in range(0, len(cells), col_count):
            row = cells[i:i + col_count]
            # 모든 형태의 개행 문자를 <br>로 치환하여 표 구조 깨짐 방지
            clean_row = []
            for c in row:
                # \r\n, \n, \r 모두 대응 및 앞뒤 공백 제거
                c_clean = c.replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>").strip()
                # 연속된 <br> 정리 및 실제 개행 제거
                while "<br><br>" in c_clean:
                    c_clean = c_clean.replace("<br><br>", "<br>")
                clean_row.append(c_clean)
                
            rows.append("| " + " | ".join(clean_row) + " |")
            
            # 헤더 구분선 추가
            if i == 0:
                rows.append("| " + " | ".join(["---"] * col_count) + " |")
                
        return "\n".join(rows)

    def _decode_text(self, data: bytes) -> str:
        """HWP PARA_TEXT 바이너리에서 제어 문자와 메타데이터를 제외한 순수 텍스트만 추출합니다."""
        if not data:
            return ""
            
        result = []
        i = 0
        while i + 1 < len(data):
            # 2바이트 단위로 읽어 UTF-16LE 문자로 처리
            char_code = struct.unpack('<H', data[i:i+2])[0]
            
            # 1. 제어 문자 처리 (HWP 5.0 Spec)
            if char_code < 32:
                # 3 (Table/Outer Control), 11 (Inline Control) 등은 뒤에 8바이트 메타데이터가 붙음
                if char_code in [1, 2, 3, 11, 15, 17, 18, 19, 20, 21, 22, 24, 25, 26]:
                    i += 16 # 제어 문자(2) + 메타데이터(14) 건너뜀 (넉넉하게 16바이트)
                else:
                    # 줄바꿈(\r\n), 탭 등만 허용
                    if char_code == 13: # CR
                        result.append('\n')
                    elif char_code == 9: # Tab
                        result.append('\t')
                    i += 2
                continue
            
            # 2. 일반 문자 처리 (제어 문자 영역 제외)
            char = chr(char_code)
            # 한자 노이즈 방지: 瑢(0x6274), 氠(0x206C) 등 tbl/pic 태그 파편 차단
            # 일반적으로 HWP의 특수 제어 코드 영역(0xFFF0 이상)도 필터링
            if char_code < 0xF800:
                result.append(char)
            i += 2
            
        return "".join(result).strip()

    def _decompress(self, data: bytes) -> bytes:
        """zlib (deflate) 압축 해제"""
        try:
            # HWP 5.0은 보통 zlib의 raw inflate (-15) 또는 기본 inflate를 사용함
            # 만약 에러 발생 시 wbits를 조정하여 재시도
            return zlib.decompress(data, -15)
        except zlib.error:
            try:
                return zlib.decompress(data)
            except zlib.error as e:
                raise ValueError(f"압축 해제 실패: {e}")

    def _parse_records(self, data: bytes) -> List[Dict]:
        """바이너리 데이터를 HWP 레코드 단위로 분축합니다."""
        records = []
        offset = 0
        total_size = len(data)
        
        while offset < total_size:
            if offset + 4 > total_size:
                break
                
            # 4바이트 헤더 읽기
            header = struct.unpack('<I', data[offset:offset+4])[0]
            tag_id = header & 0x3FF
            level = (header >> 10) & 0x3FF
            size = (header >> 20) & 0xFFF
            
            offset += 4
            
            # Extended Size 처리 (Size가 0xFFF인 경우 다음 4바이트가 실제 사이즈)
            if size == 0xFFF:
                if offset + 4 > total_size:
                    break
                size = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4
            
            # 레코드 데이터 읽기
            if offset + size > total_size:
                size = total_size - offset # 남은 데이터만큼만 읽음 (방어적 설계)
                
            record_data = data[offset:offset+size]
            records.append({
                'tag_id': tag_id,
                'level': level,
                'size': size,
                'data': record_data
            })
            
            offset += size
            
        return records

    def _extract_para_text(self, records: List[Dict]) -> str:
        """HWPTAG_PARA_TEXT 레코드에서 텍스트를 추출합니다."""
        texts = []
        for record in records:
            if record['tag_id'] == self.HWPTAG_PARA_TEXT:
                # 텍스트는 UTF-16LE 인코딩이며, 제어 문자가 포함될 수 있음
                try:
                    raw_text = record['data'].decode('utf-16-le')
                    # 제어 문자(0x0000~0x001F) 필터링 및 특수 제어 코드 처리
                    # 여기서는 단순화를 위해 가시적인 문자 위주로 추출
                    clean_text = "".join([c for c in raw_text if ord(c) >= 32 or c in '\n\r\t'])
                    texts.append(clean_text)
                except UnicodeDecodeError:
                    continue
        
        return "\n".join(texts)
