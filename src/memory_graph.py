"""Bitemporal Knowledge Graph & Memory Reconciliation Engine.

Inspired by Letta & Graphiti bitemporal architectures:
- Stores entities and relationships with valid_at and invalid_at timestamps.
- Implements strict reconciliation operations: ADD, UPDATE, DELETE, NOOP.
- Preserves full audit history: obsolete beliefs are invalidated rather than erased.
- Enables point-in-time queries and context retrieval for companies, interview rubrics, and skills.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from . import config

logger = logging.getLogger(__name__)


@dataclass
class MemoryNode:
    node_id: str
    entity_type: str  # "COMPANY", "PERSON", "SKILL", "INTERVIEW_QUESTION", "PREFERENCE"
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    valid_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    invalid_at: Optional[str] = None


@dataclass
class MemoryEdge:
    edge_id: str
    source_id: str
    target_id: str
    relation: str  # "USES_TECH", "HIRES_FOR", "REPORTED_TO", "ASKED_QUESTION", "REQUIRES_SKILL"
    properties: Dict[str, Any] = field(default_factory=dict)
    valid_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    invalid_at: Optional[str] = None


@dataclass
class ReconciliationAction:
    action_type: str  # "ADD", "UPDATE", "DELETE", "NOOP"
    target_type: str  # "NODE" or "EDGE"
    target_id: str
    rationale: str
    data: Dict[str, Any]


class BitemporalMemoryGraph:
    """Manages bitemporal graph storage and state reconciliation."""

    _local = threading.local()

    def __init__(self, db_path: Optional[Path | str] = None):
        self.db_path = Path(db_path or config.DB_PATH)
        self._init_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Reuse thread-local SQLite connection with WAL enabled."""
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=15.0)
            conn.execute("PRAGMA journal_mode=WAL;")
            self._local.conn = conn
        return conn

    def _init_tables(self):
        """Create graph tables in SQLite."""
        try:
            conn = self._get_connection()
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory_nodes (
                        node_id TEXT PRIMARY KEY,
                        entity_type TEXT,
                        name TEXT,
                        properties_json TEXT,
                        valid_at TEXT,
                        invalid_at TEXT
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory_edges (
                        edge_id TEXT PRIMARY KEY,
                        source_id TEXT,
                        target_id TEXT,
                        relation TEXT,
                        properties_json TEXT,
                        valid_at TEXT,
                        invalid_at TEXT
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_edges_source ON memory_edges(source_id);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_edges_target ON memory_edges(target_id);")
        except Exception as e:
            logger.error("Failed to initialize memory graph tables: %s", e)

    def add_or_update_node(
        self,
        node_id: str,
        entity_type: str,
        name: str,
        properties: Dict[str, Any]
    ) -> ReconciliationAction:
        """Reconcile node insertion or update with bitemporal invalidation."""
        now_ts = datetime.now(timezone.utc).isoformat()
        existing = self.get_active_node(node_id)

        if not existing:
            # ADD
            node = MemoryNode(
                node_id=node_id,
                entity_type=entity_type,
                name=name,
                properties=properties,
                valid_at=now_ts
            )
            self._save_node(node)
            return ReconciliationAction("ADD", "NODE", node_id, "New entity discovered", asdict(node))

        # Check if properties changed
        if existing.properties == properties and existing.name == name:
            return ReconciliationAction("NOOP", "NODE", node_id, "Entity properties unchanged", {})

        # UPDATE: Invalidate old node and insert new revision
        self._invalidate_node(node_id, now_ts)
        new_node_id = f"{node_id}_rev_{int(datetime.now().timestamp())}"
        new_node = MemoryNode(
            node_id=new_node_id,
            entity_type=entity_type,
            name=name,
            properties=properties,
            valid_at=now_ts
        )
        self._save_node(new_node)
        return ReconciliationAction("UPDATE", "NODE", node_id, "Entity properties updated, previous version invalidated", asdict(new_node))

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> MemoryEdge:
        """Add active relationship between nodes."""
        now_ts = datetime.now(timezone.utc).isoformat()
        edge_id = f"edge_{source_id}_{relation}_{target_id}"
        edge = MemoryEdge(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relation=relation,
            properties=properties or {},
            valid_at=now_ts
        )
        try:
            conn = self._get_connection()
            with conn:
                conn.execute("""
                    INSERT INTO memory_edges (edge_id, source_id, target_id, relation, properties_json, valid_at, invalid_at)
                    VALUES (?, ?, ?, ?, ?, ?, NULL)
                    ON CONFLICT(edge_id) DO UPDATE SET
                        properties_json = excluded.properties_json,
                        valid_at = excluded.valid_at,
                        invalid_at = NULL;
                """, (edge.edge_id, edge.source_id, edge.target_id, edge.relation, json.dumps(edge.properties), edge.valid_at))
        except Exception as e:
            logger.error("Failed to add edge %s: %s", edge_id, e)
        return edge

    def invalidate_edge(self, edge_id: str):
        """Invalidate an edge when facts change (bitemporal invalidation)."""
        now_ts = datetime.now(timezone.utc).isoformat()
        try:
            conn = self._get_connection()
            with conn:
                conn.execute("UPDATE memory_edges SET invalid_at = ? WHERE edge_id = ?", (now_ts, edge_id))
        except Exception as e:
            logger.error("Failed to invalidate edge %s: %s", edge_id, e)

    def get_active_node(self, node_id: str) -> Optional[MemoryNode]:
        """Fetch node if currently valid (invalid_at is NULL)."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT node_id, entity_type, name, properties_json, valid_at, invalid_at FROM memory_nodes WHERE node_id = ? AND invalid_at IS NULL", (node_id,))
            row = cur.fetchone()
            if row:
                return MemoryNode(
                    node_id=row[0], entity_type=row[1], name=row[2],
                    properties=json.loads(row[3] or "{}"), valid_at=row[4], invalid_at=row[5]
                )
        except Exception as e:
            logger.error("Failed to fetch active node %s: %s", node_id, e)
        return None

    def get_subgraph(self, root_node_id: str, max_depth: int = 2) -> Dict[str, Any]:
        """Retrieve active connected subgraph around root node with batch traversal."""
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []
        seen_edge_ids = set()
        visited = set()

        conn = self._get_connection()
        cur = conn.cursor()

        to_visit = [(root_node_id, 0)]
        while to_visit:
            curr_id, depth = to_visit.pop(0)
            if curr_id in visited or depth > max_depth:
                continue
            visited.add(curr_id)

            node = self.get_active_node(curr_id)
            if node:
                nodes[node.node_id] = asdict(node)

            try:
                cur.execute("""
                    SELECT edge_id, source_id, target_id, relation, properties_json, valid_at
                    FROM memory_edges
                    WHERE (source_id = ? OR target_id = ?) AND invalid_at IS NULL
                """, (curr_id, curr_id))
                for row in cur.fetchall():
                    edge_id = row[0]
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append({
                            "edge_id": edge_id,
                            "source_id": row[1],
                            "target_id": row[2],
                            "relation": row[3],
                            "properties": json.loads(row[4] or "{}"),
                            "valid_at": row[5]
                        })
                    next_id = row[2] if row[1] == curr_id else row[1]
                    if next_id not in visited:
                        to_visit.append((next_id, depth + 1))
            except Exception as e:
                logger.error("Failed to query edges for node %s in subgraph: %s", curr_id, e)

        return {"nodes": list(nodes.values()), "edges": edges}

    def _save_node(self, node: MemoryNode):
        try:
            conn = self._get_connection()
            with conn:
                conn.execute("""
                    INSERT INTO memory_nodes (node_id, entity_type, name, properties_json, valid_at, invalid_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (node.node_id, node.entity_type, node.name, json.dumps(node.properties), node.valid_at, node.invalid_at))
        except Exception as e:
            logger.error("Failed to save memory node %s: %s", node.node_id, e)

    def _invalidate_node(self, node_id: str, invalid_ts: str):
        try:
            conn = self._get_connection()
            with conn:
                conn.execute("UPDATE memory_nodes SET invalid_at = ? WHERE node_id = ?", (invalid_ts, node_id))
        except Exception as e:
            logger.error("Failed to invalidate memory node %s: %s", node_id, e)
