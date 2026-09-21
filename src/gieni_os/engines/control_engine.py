"""
Control Intelligence Engine (CIE)
Decouples legal ownership from physical/family control, classifies 5 Control Archetypes,
and generates the Knowledge Graph & Attorney Gatekeeper Bypass Strategy.
"""

from typing import List, Dict, Any, Optional
from gieni_os.domain.control import (
    ControlArchetype,
    OccupancyStatus,
    DecisionMaker,
    ControlProfile
)
from gieni_os.graph.topology import KnowledgeGraph, GraphNode, NodeType, EdgeType

class ControlEngine:
    @classmethod
    def classify_control_archetype(
        cls,
        fiduciary_name: str,
        fiduciary_address: str,
        property_situs: str,
        heir_names: List[str],
        resident_names: List[str],
        attorney_name: Optional[str] = None,
        property_id: Optional[str] = None
    ) -> ControlProfile:
        fiduciary_is_local = (
            fiduciary_address.lower().split(",")[1].strip() == property_situs.lower().split(",")[1].strip()
            if "," in fiduciary_address and "," in property_situs else True
        )
        fiduciary_is_resident = fiduciary_address.strip().lower() == property_situs.strip().lower()
        has_non_fiduciary_resident = any(r.lower() != fiduciary_name.lower() for r in resident_names)

        # Primary DM
        primary_dm = DecisionMaker(
            name=fiduciary_name,
            relationship="Personal Representative",
            is_fiduciary=True,
            is_on_site=fiduciary_is_resident,
            mailing_address=fiduciary_address,
            influence_weight=1.0
        )

        on_site_dm = None
        if has_non_fiduciary_resident:
            resident_name = resident_names[0]
            is_heir = resident_name.lower() in [h.lower() for h in heir_names]
            rel = "Resident Beneficiary" if is_heir else "Resident Caretaker / Occupant"
            on_site_dm = DecisionMaker(
                name=resident_name,
                relationship=rel,
                is_fiduciary=False,
                is_on_site=True,
                mailing_address=property_situs,
                influence_weight=0.7
            )

        # Classify the 5 Archetypes
        if len(heir_names) >= 3 and not fiduciary_is_resident:
            archetype = ControlArchetype.MODEL_3_COMMITTEE
            friction = 7
            occupancy = OccupancyStatus.HEIR_RESIDENT if has_non_fiduciary_resident else OccupancyStatus.VACANT
            bypass = "Multi-heir buy-in protocol: emphasize clean cash close to eliminate sibling buyout disputes."
        elif has_non_fiduciary_resident and not on_site_dm.is_fiduciary and not (on_site_dm.name.lower() in [h.lower() for h in heir_names]):
            archetype = ControlArchetype.MODEL_4_CARETAKER
            friction = 8
            occupancy = OccupancyStatus.ADVERSE_RESIDENT
            bypass = "Cash-for-keys / relocation allowance proposal built directly into purchase and sale agreement."
        elif not fiduciary_is_local and has_non_fiduciary_resident:
            archetype = ControlArchetype.MODEL_2_BIFURCATED
            friction = 5
            occupancy = OccupancyStatus.HEIR_RESIDENT
            bypass = "Bifurcated resolution: solve remote PR estate liquidation while coordinating local sibling move timeline."
        elif attorney_name and "public" in attorney_name.lower():
            archetype = ControlArchetype.MODEL_5_INSTITUTIONAL
            friction = 9
            occupancy = OccupancyStatus.VACANT
            bypass = "Formal institutional bid submission meeting Washington RCW 11.76 judicial appraisal standards."
        else:
            archetype = ControlArchetype.MODEL_1_UNIFIED
            friction = 2
            occupancy = OccupancyStatus.OWNER_OCCUPIED if fiduciary_is_resident else OccupancyStatus.VACANT
            bypass = "Direct fiduciary consultation: offer as-is cash sale with zero clean-out or repair requirements."

        # Attorney bypass guidance if represented
        if attorney_name:
            bypass += f" [Attorney Protocol: {attorney_name} represents probate estate. Under Washington law, PR holds independent business contracting authority under RCW 11.68 Nonintervention powers]."

        return ControlProfile(
            property_id=property_id,
            archetype=archetype,
            primary_decision_maker=primary_dm,
            on_site_resident=on_site_dm,
            occupancy_status=occupancy,
            friction_rating=friction,
            attorney_gatekeeper_name=attorney_name,
            attorney_bypass_strategy=bypass,
            all_parties=[primary_dm] + ([on_site_dm] if on_site_dm else [])
        )

    @classmethod
    def build_social_graph(
        cls,
        case_number: str,
        estate_name: str,
        property_id: str,
        profile: ControlProfile
    ) -> KnowledgeGraph:
        """Populates the Neo4j Knowledge Graph topology with nodes and edges."""
        graph = KnowledgeGraph()

        # Nodes
        estate_node = GraphNode(id=f"est_{case_number}", node_type=NodeType.ESTATE, properties={"name": estate_name})
        prop_node = GraphNode(id=property_id, node_type=NodeType.PROPERTY, properties={"occupancy": profile.occupancy_status.value})
        fiduciary_node = GraphNode(
            id=f"per_{profile.primary_decision_maker.name.lower().replace(' ', '_')}",
            node_type=NodeType.PERSON,
            properties={"name": profile.primary_decision_maker.name, "role": profile.primary_decision_maker.relationship}
        )

        graph.add_node(estate_node)
        graph.add_node(prop_node)
        graph.add_node(fiduciary_node)

        # Edges
        graph.add_edge(source_id=estate_node.id, target_id=prop_node.id, edge_type=EdgeType.OWNS)
        graph.add_edge(source_id=fiduciary_node.id, target_id=estate_node.id, edge_type=EdgeType.HAS_AUTHORITY)
        graph.add_edge(source_id=fiduciary_node.id, target_id=prop_node.id, edge_type=EdgeType.CONTROLS)

        if profile.on_site_resident:
            resident_node = GraphNode(
                id=f"per_{profile.on_site_resident.name.lower().replace(' ', '_')}",
                node_type=NodeType.PERSON,
                properties={"name": profile.on_site_resident.name, "role": profile.on_site_resident.relationship}
            )
            graph.add_node(resident_node)
            graph.add_edge(source_id=resident_node.id, target_id=prop_node.id, edge_type=EdgeType.CONTROLS)

        return graph
