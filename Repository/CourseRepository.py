from sqlalchemy.orm import Session, Query, joinedload
from ..Models.Course import Course
from ..Models.User import User

class CourseRepository:
    def __init__(self, session: Session):
        self.session = session

    def query(self, user_id: int | None = None) -> Query:
        q = self.session.query(Course)
        if user_id is not None:
            
            q = (
                q
                .join(Course.users)
                .filter(User.id == user_id)
                .distinct()
            )
        return q

    def get(self, course_id: int) -> Course | None:
        return self.session.get(Course, course_id)
