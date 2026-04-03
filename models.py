from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    tg_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    address: Optional[str]
    created_at: Optional[str]