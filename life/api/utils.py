from ..api.models import Item
from ..lib.converters import _row_to_item


def _get_item_by_content(content: str, tags: list[str] | None = None) -> Item | None:
    from .. import db  # Import db here to avoid circular dependency

    with db.get_db() as conn:
        query = "SELECT id, content, focus, due_date, created, completed, is_habit FROM items WHERE content = ?"
        params = [content]

        if tags:
            tag_placeholders = ", ".join(["?"] * len(tags))
            query += f" AND id IN (SELECT item_id FROM tags WHERE tag IN ({tag_placeholders}))"
            params.extend(tags)

        cursor = conn.execute(query, tuple(params))
        row = cursor.fetchone()
        if row:
            return _row_to_item(row)
    return None
