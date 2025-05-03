from sqlalchemy.orm import Session
from ..Models.Lesson import Lesson

class LessonRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, lesson_id: int) -> Lesson | None:
        return (
            self.session
                .query(Lesson)
                .filter(Lesson.id == lesson_id)
                .first()
        )

    def get_next_by_id(self, lesson_id: int) -> Lesson | None:
        lesson = self.get(lesson_id)
        if not lesson:
            return None
        
        return lesson.get_next_lesson(self.session)
