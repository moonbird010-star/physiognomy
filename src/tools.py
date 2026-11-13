"""도메인 도구 (제출 규약 진입점).

실제 코드는 도메인별 폴더에 있다. 제출 규약이 src/tools.py 를 요구하므로 여기서 다시 내보낸다.
- 사진 분석: src/face_analysis/tools.py   (analyze_face_photo)
- 풀이:      src/reading/tools.py         (search_reading_docs, find_similar_animals, find_similar_king)
- 운세:      src/fortune/tools.py         (get_fortune)
"""
from src.face_analysis.tools import analyze_face_photo
from src.fortune.tools import get_fortune
from src.reading.tools import find_similar_animals, find_similar_king, search_reading_docs

TOOLS = [analyze_face_photo, search_reading_docs, find_similar_animals, find_similar_king, get_fortune]
