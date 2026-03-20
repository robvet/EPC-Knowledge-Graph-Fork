"""In-memory graph client that mirrors the Cosmos DB Gremlin API contract.

In *mock* mode (default) everything lives in dictionaries.  When APP_MODE=azure
the class would be swapped for a real gremlinpython-based client — the public
API stays identical so agents and queries never change.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel


class GraphClient:
    """Lightweight in-memory property-graph store.

    Vertices are keyed by ``(label, id)``; edges by ``(label, from_id, to_id)``.
    All property values are stored as-is (primitives / strings / dates converted
    to ISO strings on insertion via Pydantic ``.model_dump(mode='json')``).
    """

    def __init__(self) -> None:
        # {vertex_id: {"label": str, **properties}}
        self._vertices: Dict[str, Dict[str, Any]] = {}
        # list of {"label": str, "from_id": str, "to_id": str, **properties}
        self._edges: List[Dict[str, Any]] = []
        # adjacency: from_id -> [(edge_label, to_id, edge_props)]
        self._adj: Dict[str, List[Tuple[str, str, Dict]]] = defaultdict(list)
        # reverse adjacency: to_id -> [(edge_label, from_id, edge_props)]
        self._rev: Dict[str, List[Tuple[str, str, Dict]]] = defaultdict(list)

    # ── Vertices ────────────────────────────────────────────────────────

    def add_vertex(self, label: str, model: BaseModel) -> Dict[str, Any]:
        """Insert or upsert a vertex from a Pydantic model."""
        data = model.model_dump(mode="json")
        vid = data["id"]
        data["_label"] = label
        self._vertices[vid] = data
        return data

    def get_vertex(self, vid: str) -> Optional[Dict[str, Any]]:
        return self._vertices.get(vid)

    def get_vertices_by_label(self, label: str) -> List[Dict[str, Any]]:
        return [v for v in self._vertices.values() if v.get("_label") == label]

    def find_vertices(self, label: str, **filters: Any) -> List[Dict[str, Any]]:
        """Return vertices matching label + property equality filters."""
        result = []
        for v in self._vertices.values():
            if v.get("_label") != label:
                continue
            if all(v.get(k) == val for k, val in filters.items()):
                result.append(v)
        return result

    def update_vertex(self, vid: str, **props: Any) -> Optional[Dict[str, Any]]:
        v = self._vertices.get(vid)
        if v is None:
            return None
        v.update(props)
        return v

    # ── Edges ───────────────────────────────────────────────────────────

    def add_edge(
        self,
        label: str,
        from_id: str,
        to_id: str,
        **properties: Any,
    ) -> Dict[str, Any]:
        edge = {"_label": label, "from_id": from_id, "to_id": to_id, **properties}
        self._edges.append(edge)
        self._adj[from_id].append((label, to_id, properties))
        self._rev[to_id].append((label, from_id, properties))
        return edge

    def add_edge_from_model(self, label: str, model: BaseModel) -> Dict[str, Any]:
        data = model.model_dump(mode="json")
        from_id = data.pop("from_id")
        to_id = data.pop("to_id")
        return self.add_edge(label, from_id, to_id, **data)

    def get_edges(
        self,
        label: Optional[str] = None,
        from_id: Optional[str] = None,
        to_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = self._edges
        if label:
            results = [e for e in results if e["_label"] == label]
        if from_id:
            results = [e for e in results if e["from_id"] == from_id]
        if to_id:
            results = [e for e in results if e["to_id"] == to_id]
        return results

    # ── Traversal helpers ───────────────────────────────────────────────

    def outgoing(self, vid: str, edge_label: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return vertices reachable from *vid* via outgoing edges."""
        targets = self._adj.get(vid, [])
        if edge_label:
            targets = [(l, t, p) for l, t, p in targets if l == edge_label]
        return [self._vertices[t] for _, t, _ in targets if t in self._vertices]

    def incoming(self, vid: str, edge_label: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return vertices that point *to* vid via incoming edges."""
        sources = self._rev.get(vid, [])
        if edge_label:
            sources = [(l, s, p) for l, s, p in sources if l == edge_label]
        return [self._vertices[s] for _, s, _ in sources if s in self._vertices]

    def neighbors(self, vid: str, edge_label: Optional[str] = None) -> List[Dict[str, Any]]:
        """All vertices connected in either direction."""
        out_set = {v["id"] for v in self.outgoing(vid, edge_label)}
        inc_set = {v["id"] for v in self.incoming(vid, edge_label)}
        all_ids = out_set | inc_set
        return [self._vertices[i] for i in all_ids if i in self._vertices]

    # ── Bulk & serialization ────────────────────────────────────────────

    def vertex_count(self) -> int:
        return len(self._vertices)

    def edge_count(self) -> int:
        return len(self._edges)

    def summary(self) -> Dict[str, int]:
        """Return counts by vertex label."""
        counts: Dict[str, int] = defaultdict(int)
        for v in self._vertices.values():
            counts[v.get("_label", "unknown")] += 1
        return dict(counts)

    def to_d3_json(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Export graph as D3.js-compatible ``{nodes, links}`` JSON."""
        nodes = []
        for vid, v in self._vertices.items():
            node = {
                "id": vid,
                "label": v.get("_label", ""),
                "name": v.get("name", v.get("tag_number", v.get("po_number", vid))),
                "properties": {k: val for k, val in v.items()
                               if k != "_label"},
            }
            nodes.append(node)
        links = []
        for e in self._edges:
            link = {
                "source": e["from_id"],
                "target": e["to_id"],
                "label": e.get("_label", ""),
                "properties": {k: val for k, val in e.items()
                               if k not in ("_label", "from_id", "to_id")},
            }
            links.append(link)
        return {"nodes": nodes, "links": links}

    def clear(self) -> None:
        self._vertices.clear()
        self._edges.clear()
        self._adj.clear()
        self._rev.clear()


# ── Module-level singleton ──────────────────────────────────────────────────

_graph: Optional[GraphClient] = None


def get_graph() -> GraphClient:
    """Return (and lazily create) the singleton graph client."""
    global _graph
    if _graph is None:
        _graph = GraphClient()
    return _graph
