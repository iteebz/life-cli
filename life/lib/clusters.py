from collections import deque

from life.models import Task

__all__ = [
    "build_clusters",
    "cluster_focus",
    "link_distances",
]


def build_clusters(tasks: list[Task], links: list[tuple[str, str]]) -> list[list[Task]]:
    """Group tasks into connected components via link graph. Returns list of clusters (each a list of Tasks). Singletons (no links) are excluded."""
    task_map = {t.id: t for t in tasks}
    adj: dict[str, set[str]] = {t.id: set() for t in tasks}
    for from_id, to_id in links:
        if from_id in adj and to_id in adj:
            adj[from_id].add(to_id)
            adj[to_id].add(from_id)

    visited: set[str] = set()
    clusters: list[list[Task]] = []

    for task in tasks:
        if task.id in visited or not adj[task.id]:
            continue
        component: list[Task] = []
        queue = deque([task.id])
        while queue:
            tid = queue.popleft()
            if tid in visited:
                continue
            visited.add(tid)
            if tid in task_map:
                component.append(task_map[tid])
            for neighbor in adj[tid]:
                if neighbor not in visited:
                    queue.append(neighbor)
        if len(component) > 1:
            clusters.append(component)

    return clusters


def cluster_focus(cluster: list[Task]) -> Task | None:
    """Return the focused task in a cluster, or None."""
    for task in cluster:
        if task.focus:
            return task
    return None


def link_distances(focus_id: str, links: list[tuple[str, str]]) -> dict[str, int]:
    """BFS from focus_id. Returns {task_id: hop_count} for reachable tasks."""
    adj: dict[str, set[str]] = {}
    for from_id, to_id in links:
        adj.setdefault(from_id, set()).add(to_id)
        adj.setdefault(to_id, set()).add(from_id)

    distances: dict[str, int] = {focus_id: 0}
    queue = deque([focus_id])
    while queue:
        current = queue.popleft()
        for neighbor in adj.get(current, set()):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                queue.append(neighbor)
    return distances
