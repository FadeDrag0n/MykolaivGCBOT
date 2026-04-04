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

@dataclass
class Category:
    id: int
    name: str
    type: str  # 'animals' | 'plants'

@dataclass
class Product:
    id: int
    category_id: int
    name: str
    price: float
    description: Optional[str] = None
    stock: int = 0
    photo_id: Optional[str] = None