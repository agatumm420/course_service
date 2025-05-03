
from sqlalchemy.orm import Session
from ..Models.User import User

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)
