from typing import Optional
from datetime import datetime

class User:
    def __init__(
        self,
        id: str,
        email: str,
        username: str,
        fullName: str,
        password: str,
    ):
        self.id = id
        self.email = email
        self.username = username
        self.fullName = fullName
        self.password = password

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "fullName": self.fullName,
        }