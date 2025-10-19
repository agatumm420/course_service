from sqlalchemy.orm import Session
from ..Models.LessonData import LessonData
from sqlalchemy.orm.exc import NoResultFound

class LessonDataRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_lesson_id(self, lesson_id: int) -> LessonData | None:
        try:
            return (
                self.session
                    .query(LessonData)
                    .filter(LessonData.lesson_id == lesson_id)
                    .one()
            )
        except NoResultFound:
            return None

    def create(self, lesson_id: int, course_data_id: int, data: dict) -> LessonData:
        ld = LessonData(
            lesson_id=lesson_id,
            course_data_id=course_data_id,
            data=data
        )
        self.session.add(ld)
        return ld
