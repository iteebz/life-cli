import itertools
import sys
import threading
import time
from datetime import date, datetime

from ..config import get_countdowns
from ..core.tag import get_tags
from ..lib.ansi import ANSI
from ..lib.format import format_decay, format_due


class Spinner:
    """Simple CLI spinner for async feedback."""

    def __init__(self, persona: str = "roast"):
        self.stop_event = threading.Event()
        self.spinner_frames = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
        self.persona = persona
        self.thread = None

    def _animate(self):
        """Run spinner animation in background thread."""
        actions = {"roast": "roasting", "pepper": "peppering", "kim": "investigating"}
        action = actions.get(self.persona, "thinking")
        while not self.stop_event.is_set():
            frame = next(self.spinner_frames)
            sys.stderr.write(f"\r{frame} {action}... ")
            sys.stderr.flush()
            time.sleep(0.1)
        sys.stderr.write("\r" + " " * 30 + "\r")
        sys.stderr.flush()

    def start(self):
        """Start the spinner."""
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the spinner."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=0.5)


def render_today_completed(today_items):
    """Render today's completed tasks only (habits/chores handled at bottom)"""
    if not today_items:
        return ""

    tasks_only = [
        item
        for item in today_items
        if not any(tag in ("habit", "chore") for tag in get_tags(item[0]))
    ]

    if not tasks_only:
        return ""

    lines = [f"\n{ANSI.BOLD}{ANSI.GREEN}✅ DONE TODAY:{ANSI.RESET}"]

    for item in tasks_only:
        item_id = item[0]
        content = item[1]
        time_str = f" {format_decay(item[2])}" if item[2] else ""
        tags = get_tags(item_id)
        tags_str = " " + " ".join(f"{ANSI.GREY}#{t}{ANSI.RESET}" for t in tags) if tags else ""
        lines.append(f"  ✓ {content.lower()}{tags_str}{time_str}")

    return "\n".join(lines)


def render_dashboard(items, today_breakdown, momentum_7d, context, today_items=None):
    """Render full dashboard view"""
    habits_today, tasks_today, chores_today = today_breakdown
    habits_avg, tasks_avg, chores_avg = momentum_7d
    today = date.today()
    now = datetime.now().astimezone()
    current_time = now.strftime("%H:%M")

    lines = []
    lines.append(f"\nToday: {today} {current_time}")
    countdowns = get_countdowns()
    if countdowns:
        upcoming = sorted(countdowns, key=lambda x: x["date"])
        next_cd = upcoming[0]
        days = (date.fromisoformat(next_cd["date"]) - today).days
        emoji = next_cd.get("emoji", "📌")
        name = next_cd.get("name", "event")
        lines.append(f"{emoji} {days} days until {name}!")

    lines.append(f"\nhabits: {habits_today} | tasks: {tasks_today} | chores: {chores_today}")
    lines.append(
        f"momentum: {habits_avg:.1f} habits/day | {tasks_avg:.1f} tasks/day | {chores_avg:.1f} chores/day"
    )

    if today_items:
        lines.append(render_today_completed(today_items))

    habits = []
    chores = []
    regular_items = []

    for item in items:
        item_id = item[0]
        item_tags = get_tags(item_id)
        if "habit" in item_tags:
            habits.append(item)
        elif "chore" in item_tags:
            chores.append(item)
        else:
            regular_items.append(item)

    all_habits = [t for t in habits if t[5] is not None and date.fromisoformat(t[5][:10]) >= today]
    if all_habits or habits:
        checked_today = len(
            {item[0] for item in (today_items or []) if "habit" in get_tags(item[0])}
        )
        lines.append(
            f"\n{ANSI.BOLD}{ANSI.WHITE}HABITS ({checked_today}/{len(habits)}):{ANSI.RESET}"
        )
        today_habit_ids = {item[0] for item in (today_items or []) if "habit" in get_tags(item[0])}
        undone_habits = [h for h in habits if h[0] not in today_habit_ids]
        done_habits = [h for h in habits if h[0] in today_habit_ids]
        sorted_habits = sorted(undone_habits, key=lambda x: x[1].lower()) + sorted(
            done_habits, key=lambda x: x[1].lower()
        )
        for item in sorted_habits:
            content = item[1]
            last_checked = item[5] if len(item) > 5 else None
            decay = format_decay(last_checked) if last_checked else ""
            decay_str = f" {decay}" if decay else ""
            if item[0] in today_habit_ids:
                lines.append(f"  {ANSI.GREY}✓ {content.lower()}{decay_str}{ANSI.RESET}")
            else:
                lines.append(f"  □ {content.lower()}{decay_str}")

    all_chores = [t for t in chores if t[5] is not None and date.fromisoformat(t[5][:10]) >= today]
    if all_chores or chores:
        chores_checked_today = len(
            {item[0] for item in (today_items or []) if "chore" in get_tags(item[0])}
        )
        lines.append(
            f"\n{ANSI.BOLD}{ANSI.WHITE}CHORES ({chores_checked_today}/{len(chores)}):{ANSI.RESET}"
        )
        today_chore_ids = {item[0] for item in (today_items or []) if "chore" in get_tags(item[0])}
        undone_chores = [c for c in chores if c[0] not in today_chore_ids]
        done_chores = [c for c in chores if c[0] in today_chore_ids]
        sorted_chores = sorted(undone_chores, key=lambda x: x[1].lower()) + sorted(
            done_chores, key=lambda x: x[1].lower()
        )
        for item in sorted_chores:
            content = item[1]
            last_checked = item[5] if len(item) > 5 else None
            decay = format_decay(last_checked) if last_checked else ""
            decay_str = f" {decay}" if decay else ""
            if item[0] in today_chore_ids:
                lines.append(f"  {ANSI.GREY}✓ {content.lower()}{decay_str}{ANSI.RESET}")
            else:
                lines.append(f"  □ {content.lower()}{decay_str}")

    if not regular_items:
        lines.append("\nNo pending items. You're either productive or fucked.")
    else:
        today = date.today()

        tagged_regular = {}
        untagged = []

        for item in regular_items:
            item_id = item[0]
            item_tags = get_tags(item_id)
            filtered_tags = [t for t in item_tags if t not in ("habit", "chore")]
            if filtered_tags:
                for tag in filtered_tags:
                    if tag not in tagged_regular:
                        tagged_regular[tag] = []
                    tagged_regular[tag].append(item)
            else:
                untagged.append(item)

        def sort_items(item_list):
            return sorted(
                item_list, key=lambda x: (not x[2], x[3] is None, x[3] or "", x[1].lower())
            )

        for idx, tag in enumerate(sorted(tagged_regular.keys())):
            items_by_tag = sort_items(tagged_regular[tag])
            tag_color = ANSI.POOL[idx % len(ANSI.POOL)]
            lines.append(
                f"\n{ANSI.BOLD}{tag_color}#{tag.upper()} ({len(items_by_tag)}):{ANSI.RESET}"
            )
            for item in items_by_tag:
                item_id, content, _focus, due = item[:4]
                due_str = format_due(due) if due else ""
                other_tags = [
                    t for t in get_tags(item_id) if t != tag and t not in ("habit", "chore")
                ]
                tags_str = " " + " ".join(f"#{t}" for t in other_tags) if other_tags else ""
                indicator = f"{ANSI.BOLD}🔥{ANSI.RESET} " if _focus else ""
                due_part = f"{due_str} " if due_str else ""
                lines.append(f"  {indicator}{due_part}{content.lower()}{tags_str}")

        untagged_sorted = sort_items(untagged)
        if untagged_sorted:
            lines.append(f"\n{ANSI.BOLD}{ANSI.DIM}BACKLOG ({len(untagged_sorted)}):{ANSI.RESET}")
            for item in untagged_sorted:
                item_id, content, _focus, due = item[:4]
                due_str = format_due(due) if due else ""
                indicator = f"{ANSI.BOLD}🔥{ANSI.RESET} " if _focus else ""
                due_part = f"{due_str} " if due_str else ""
                lines.append(f"  {indicator}{due_part}{content.lower()}")

    return "\n".join(lines)


def render_item_list(items):
    """Render item list view with IDs"""
    if not items:
        return "No pending items."

    lines = []
    for item in items:
        item_id, content, focus, due = item[:4]
        focus_label = "🔥" if focus else ""
        due_str = format_due(due) if due else ""
        due_part = f"{due_str} " if due_str else ""
        tags = get_tags(item_id)
        tags_str = " " + " ".join(f"#{tag}" for tag in tags) if tags else ""
        lines.append(f"{item_id}: {focus_label}{due_part}{content.lower()}{tags_str}")

    return "\n".join(lines)


def render_focus_items(items):
    """Render focused items list"""
    if not items:
        return f"{ANSI.GREY}No focus items. Time to focus on something.{ANSI.RESET}"

    lines = [f"{ANSI.BOLD}{ANSI.YELLOW}🔥 FOCUS ITEMS:{ANSI.RESET}\n"]
    for item in items:
        item_id, content, _, due = item[:4]
        due_str = format_due(due) if due else ""
        due_part = f"{due_str} " if due_str else ""
        tags = get_tags(item_id)
        tags_str = " " + " ".join(f"{ANSI.GREY}#{tag}{ANSI.RESET}" for tag in tags) if tags else ""
        lines.append(f"  • {due_part}{content.lower()}{tags_str}")

    return "\n".join(lines)
