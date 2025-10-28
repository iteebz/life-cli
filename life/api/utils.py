from datetime import date, datetime

from ..api.models import Item


def _row_to_item(row) -> Item:
    return Item(
        id=row[0],
        content=row[1],
        focus=bool(row[2]),
        due=date.fromisoformat(row[3]) if isinstance(row[3], str) else None,
        created=datetime.fromtimestamp(row[4])
        if isinstance(row[4], (int, float))
        else datetime.min,
        completed=date.fromisoformat(row[5])
        if isinstance(row[5], str) and row[5]
        else None,
        is_repeat=bool(row[6]) if len(row) > 6 else False,
    )


def _get_item_by_content(content: str, tags: list[str] | None = None) -> Item | None:
    from .. import db # Import db here to avoid circular dependency

    with db.get_db() as conn:
        query = "SELECT id, content, focus, due, created, completed, is_repeat FROM items WHERE content = ?"
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
