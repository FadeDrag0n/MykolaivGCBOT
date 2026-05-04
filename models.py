from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum

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

@dataclass
class CartItem:
    id: int
    tg_id: int
    product_id: int
    quantity: int
    product_name: Optional[str] = None
    product_price: Optional[float] = None
    product_photo_id: Optional[str] = None
    product_stock: Optional[int] = None

class OrderStatus(Enum):
    NEW            = "new"
    PENDING        = "pending"
    IN_PROGRESS    = "in_progress"
    PAID           = "paid"
    PACKED         = "packed"
    SHIPPED        = "shipped"
    READY          = "ready"
    DONE           = "done"
    CANCELLED      = "cancelled"
    RETURNED       = "returned"

ORDER_STATUS_LABELS = {
    OrderStatus.NEW:         "🆕 Нове",
    OrderStatus.PENDING:     "⏳ Очікує підтвердження",
    OrderStatus.IN_PROGRESS: "🔧 В обробці",
    OrderStatus.PAID:        "💳 Оплачено",
    OrderStatus.PACKED:      "📦 Укомплектовано",
    OrderStatus.SHIPPED:     "🚚 Відправлено",
    OrderStatus.READY:       "🏪 Очікує у пункті видачі",
    OrderStatus.DONE:        "✅ Виконано",
    OrderStatus.CANCELLED:   "❌ Скасовано",
    OrderStatus.RETURNED:    "↩️ Повернуто",
}

# Статуси які вважаються "активними" (не фінальними)
ACTIVE_STATUSES = {
    OrderStatus.NEW, OrderStatus.PENDING, OrderStatus.IN_PROGRESS,
    OrderStatus.PAID, OrderStatus.PACKED, OrderStatus.SHIPPED, OrderStatus.READY,
}

# Статуси при яких клієнт може скасувати замовлення
CANCELLABLE_BY_USER = {OrderStatus.NEW, OrderStatus.PENDING}

@dataclass
class OrderItem:
    id: int
    order_id: int
    product_id: int
    product_name: str
    price: float
    quantity: int

@dataclass
class Order:
    id: int
    tg_id: int
    status: str
    phone: str
    address: Optional[str]
    comment: Optional[str]
    total: float
    created_at: str
    ttn: Optional[str] = None          # номер накладної Нова Пошта
    items: List[OrderItem] = field(default_factory=list)
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None