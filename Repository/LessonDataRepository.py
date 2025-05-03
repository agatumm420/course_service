from sqlalchemy.orm import Session
from ..Models.LessonData import LessonData

class LessonDataRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, lesson_id: int, course_data_id: int, data: dict) -> LessonData:
        ld = LessonData(
            lesson_id=lesson_id,
            course_data_id=course_data_id,
            data=data
        )
        self.session.add(ld)
        return ld
