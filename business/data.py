PRODUCTS = [
    {"id": 1, "name": "Ноутбук Lenovo ThinkPad", "price": 89990, "owner": "manager@example.com"},
    {"id": 2, "name": "Смартфон Pixel 9", "price": 64990, "owner": "manager@example.com"},
    {"id": 3, "name": "Наушники Sony WH-1000XM6", "price": 24990, "owner": "user@example.com"},
]

STORES = [
    {"id": 1, "name": "Магазин на Ленина, 10", "city": "Москва", "owner": "admin@example.com"},
    {"id": 2, "name": "Магазин на Мира, 5", "city": "Казань", "owner": "manager@example.com"},
]

ORDERS = [
    {"id": 1, "product_id": 1, "quantity": 1, "status": "оплачен", "owner": "user@example.com"},
    {"id": 2, "product_id": 3, "quantity": 2, "status": "в сборке", "owner": "user@example.com"},
    {"id": 3, "product_id": 2, "quantity": 1, "status": "доставлен", "owner": "manager@example.com"},
]
