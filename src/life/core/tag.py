"""Tag operations for items."""

import sqlite3
import uuid

from ..lib.sqlite import DB_PATH, init_db


def add_tag(item_id, tag):
	"""Add a tag to an item"""
	init_db()
	conn = sqlite3.connect(DB_PATH)
	try:
		conn.execute(
			"INSERT INTO item_tags (id, item_id, tag) VALUES (?, ?, ?)",
			(str(uuid.uuid4()), item_id, tag.lower()),
		)
		conn.commit()
	except sqlite3.IntegrityError:
		pass
	finally:
		conn.close()


def get_tags(item_id):
	"""Get all tags for an item"""
	init_db()
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.execute("SELECT tag FROM item_tags WHERE item_id = ?", (item_id,))
	tags = [row[0] for row in cursor.fetchall()]
	conn.close()
	return tags


def get_items_by_tag(tag):
	"""Get all pending items with a specific tag"""
	init_db()
	conn = sqlite3.connect(DB_PATH)
	cursor = conn.execute(
		"""
		SELECT i.id, i.content, i.focus, i.due, i.created, MAX(c.checked), COUNT(c.id), i.target_count
		FROM items i
		LEFT JOIN checks c ON i.id = c.item_id
		INNER JOIN item_tags it ON i.id = it.item_id
		WHERE i.completed IS NULL AND it.tag = ?
		GROUP BY i.id
		ORDER BY i.focus DESC, i.due ASC NULLS LAST, i.created ASC
	""",
		(tag.lower(),),
	)
	items = cursor.fetchall()
	conn.close()
	return items


def remove_tag(item_id, tag):
	"""Remove a tag from an item"""
	init_db()
	conn = sqlite3.connect(DB_PATH)
	conn.execute(
		"DELETE FROM item_tags WHERE item_id = ? AND tag = ?",
		(item_id, tag.lower()),
	)
	conn.commit()
	conn.close()


def manage_tag(tag_name, item_partial=None, remove=False):
	"""Add/remove tag from item, or list items by tag. Returns message string."""
	from ..app.render import render_item_list
	from ..lib.match import find_item
	
	if item_partial:
		item = find_item(item_partial)
		if item:
			if remove:
				remove_tag(item[0], tag_name)
				return f"Untagged: {item[1]} ← #{tag_name}"
			else:
				add_tag(item[0], tag_name)
				return f"Tagged: {item[1]} → #{tag_name}"
		else:
			return f"No match for: {item_partial}"
	else:
		items = get_items_by_tag(tag_name)
		if items:
			return f"\n{tag_name.upper()} ({len(items)}):\n{render_item_list(items)}"
		else:
			return f"No items tagged with #{tag_name}"
