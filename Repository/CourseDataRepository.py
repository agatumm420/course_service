
from sqlalchemy.orm import Session
from ..Models.CourseData import CourseData

class CourseDataRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id: int, course_id: int) -> CourseData:
        cd = CourseData(user_id=user_id, course_id=course_id)
        self.session.add(cd)
        self.session.flush()   
        return cd
    def set_current_lesson(self, course_data_id: int, lesson_id: int) -> None:
        cd = self.session.get(CourseData, course_data_id)
        if cd:
            cd.current_lesson_id = lesson_id
    def get_by_user_and_course(self, user_id: int, course_id: int) -> CourseData | None:
        return (
            self.session
                .query(CourseData)
                .filter(
                    CourseData.user_id   == user_id,
                    CourseData.course_id == course_id
                )
                .first()
        )