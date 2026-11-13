"""사진 분석 스키마: 비전 모델의 구조화 출력."""
from typing import Literal

from pydantic import BaseModel, Field


class FaceAnalysis(BaseModel):
    """사진 분석 결과 (비전 모델 구조화 출력)."""

    human_face_count: int = Field(description="사진 속 사람 얼굴 수 (배경에 작게 찍힌 사람 포함). 동물·풍경만 있으면 0")
    main_subject: Literal["one_main_face", "several_similar_faces", "none"] = Field(
        description=(
            "one_main_face: 한 얼굴이 가장 크고 가까이 있어 사진의 주인공이 분명하다 (셀카·카메라 촬영). "
            "뒤쪽에 작게 찍히거나 일부만 보이는 사람은 배경이므로 이 판단에 영향을 주지 않는다. "
            "several_similar_faces: 비슷한 크기의 얼굴이 둘 이상 나란히 있어 주인공을 정할 수 없다 (함께 찍은 사진). "
            "none: 사람 얼굴이 없다"
        )
    )
    quality: Literal["good", "dark_or_blurry"] = Field(description="주인공 얼굴의 생김새를 알아볼 수 있으면 good")
    forehead: Literal["넓고 반듯한 이마", "좁은 이마", "둥글고 볼록한 이마"]
    eyes: Literal["크고 동그란 눈", "가늘고 긴 눈", "올라간 눈꼬리", "내려간 눈꼬리"]
    nose: Literal["곧은 콧대", "두툼한 콧방울", "둥근 코끝"]
    mouth: Literal["올라간 입꼬리", "두툼한 입술", "크고 시원한 입", "작고 단정한 입"]
    ears: Literal["크고 귓불이 두툼한 귀", "작고 단단한 귀", "위치가 높은 귀"]
