import olefile
import os

class HWPOLEReader:
    """
    HWP(OLE2) 파일을 분석하여 내부 스트림 목록 및 데이터를 제공하는 클래스.

    REQ-ID: REQ-101-01
    """
    def __init__(self, file_path: str):
        # [SEC-101] 파일 존재 여부 사전 검증 — 경로 조작 방지를 위한 os.path.exists 사용
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        self.file_path = file_path
        self.ole = None

    def open(self) -> bool:
        """
        OLE 컨테이너를 오픈하고 HWP 시그니처를 확인합니다.

        Returns:
            파일 오픈 성공 시 True
        Raises:
            ValueError: 유효한 OLE2 파일이 아니거나 HWP FileHeader 스트림이 없는 경우
        """
        # [SEC-102] 파일 시그니처(OLE2 매직 바이트) 검증 — 임의 바이너리 파일 처리 방지
        if not olefile.isOleFile(self.file_path):
            raise ValueError(f"유효한 OLE2 파일이 아닙니다: {self.file_path}")

        self.ole = olefile.OleFileIO(self.file_path)

        # HWP 시그니처 확인 (FileHeader 스트림 존재 여부)
        if not self.ole.exists('FileHeader'):
             self.close()
             raise ValueError("HWP 파일 형식이 아닙니다 (FileHeader 스트림 누락)")

        return True

    def list_streams(self) -> list[str]:
        """
        전체 스트림 및 스토리지 목록을 반환합니다.

        Returns:
            '/'로 구분된 스트림/스토리지 경로 문자열 리스트
        Raises:
            RuntimeError: 파일이 오픈되지 않은 상태에서 호출된 경우
        """
        if not self.ole:
            raise RuntimeError("파일이 오픈되지 않았습니다.")
        return ["/".join(entry) for entry in self.ole.listdir()]

    def get_bodytext_streams(self) -> list[str]:
        """
        본문 데이터가 담긴 BodyText 하위 스트림 목록을 반환합니다.

        Returns:
            'BodyText/'로 시작하는 스트림 경로 문자열 리스트
        Raises:
            RuntimeError: 파일이 오픈되지 않은 상태에서 호출된 경우
        """
        if not self.ole:
            raise RuntimeError("파일이 오픈되지 않았습니다.")

        streams = self.list_streams()
        return [s for s in streams if s.startswith('BodyText/')]

    def get_stream_data(self, stream_name: str) -> bytes:
        """
        특정 스트림의 바이너리 데이터를 읽어옵니다.

        Args:
            stream_name: 읽어올 스트림의 경로 문자열
        Returns:
            스트림의 원시 바이너리 데이터
        Raises:
            RuntimeError: 파일이 오픈되지 않은 상태에서 호출된 경우
            KeyError: 지정한 스트림이 존재하지 않는 경우
        """
        if not self.ole:
            raise RuntimeError("파일이 오픈되지 않았습니다.")

        if not self.ole.exists(stream_name):
            raise KeyError(f"스트림을 찾을 수 없습니다: {stream_name}")

        with self.ole.openstream(stream_name) as s:
            return s.read()

    def close(self):
        """OLE 컨테이너를 닫습니다."""
        if self.ole:
            self.ole.close()
            self.ole = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
