"""
Gieni OS Graph Topology (Neo4j Semantics)
Models property, estate, heir, fiduciary, and legal counsel relationships.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

class NodeType(Enum):
    ESTATE = "Estate"
    PERSON = "Person"
    PROPERTY = "Property"
    AUTHORITY_CANDIDATE = "AuthorityCandidate"
    CONTROLLER = "Controller"

class EdgeType(Enum):
    REPRESENTS = "REPRESENTS"
    CONTROLS = "CONTROLS"
    HAS_AUTHORITY = "HAS_AUTHORITY"
    OWNS = "OWNS"
    HEIR_TO = "HEIR_TO"

@dataclass
class GraphNode:
    id: str
    node_type: NodeType
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: Dict[str, Any] = field(default_factory=dict)

from collections import defaultdict

class KnowledgeGraph:
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._target_to_edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self._source_to_edges: Dict[str, List[GraphEdge]] = defaultdict(list)

    def add_node(self, node: GraphNode) -> None:
        if isinstance(node, GraphNode):
            self.nodes[node.id] = node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        edge = GraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            properties=properties or {}
        )
        self.edges.append(edge)
        self._target_to_edges[target_id].append(edge)
        self._source_to_edges[source_id].append(edge)

    def find_controller(self, property_id: str) -> Optional[GraphNode]:
        for edge in self._target_to_edges.get(property_id, []):
            if edge.edge_type in (EdgeType.CONTROLS, EdgeType.OWNS):
                return self.nodes.get(edge.source_id)
        return None

    def find_authority(self, property_id: str) -> Optional[GraphNode]:
        for edge in self._target_to_edges.get(property_id, []):
            if edge.edge_type == EdgeType.HAS_AUTHORITY:
                return self.nodes.get(edge.source_id)
        return None

    def find_attorney(self, estate_id: str) -> Optional[GraphNode]:
        for edge in self._target_to_edges.get(estate_id, []):
            if edge.edge_type == EdgeType.REPRESENTS:
                return self.nodes.get(edge.source_id)
        return None

    def export_cypher(self) -> str:
        def esc(val: Any) -> str:
            if isinstance(val, (int, float, bool)):
                return str(val)
            s = str(val).replace("\\", "\\\\").replace("'", "\\'")
            return f"'{s}'"

        lines = ["// Gieni Knowledge Graph Export"]
        for node in self.nodes.values():
            node_id_esc = str(node.id).replace("\\", "\\\\").replace("'", "\\'")
            prop_items = []
            for k, v in node.properties.items():
                if isinstance(v, (str, int, float, bool)):
                    safe_k = str(k).replace("`", "").replace("'", "")
                    prop_items.append(f"{safe_k}: {esc(v)}")
            props_str = f"id: '{node_id_esc}'" + (", " + ", ".join(prop_items) if prop_items else "")
            lines.append(f"CREATE (n:{node.node_type.value} {{{props_str}}});")
        for edge in self.edges:
            src_esc = str(edge.source_id).replace("\\", "\\\\").replace("'", "\\'")
            tgt_esc = str(edge.target_id).replace("\\", "\\\\").replace("'", "\\'")
            lines.append(f"MATCH (a {{id: '{src_esc}'}}), (b {{id: '{tgt_esc}'}}) CREATE (a)-[:{edge.edge_type.value}]->(b);")
        return "\n".join(lines)
