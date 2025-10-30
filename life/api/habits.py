from .items import add_item, get_all_items, get_item
from .models import Item
from .tags import get_tags


def add_habit(description: str) -> Item:
    # Placeholder for adding a habit. This will likely call add_item with habit-specific logic.
    # For now, just adding a basic item with a 'habit' tag.
    return add_item(description, tags=["habit"], is_repeat=True)


def is_habit(item_id: str) -> bool:
    item = get_item(item_id)
    if not item:
        return False
    return item.is_habit and "habit" in get_tags(item.id)


def get_habits() -> list[Item]:
    all_items = get_all_items()
    habits = []
    for item in all_items:
        if item.is_habit and "habit" in get_tags(item.id):
            habits.append(item)
    return habits
