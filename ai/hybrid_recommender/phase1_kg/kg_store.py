"""KG 저장소 추상화: Neo4jKGStore / NetworkXKGStore

Neo4j 가 설치되지 않은 환경에서는 NetworkX 로 자동 폴백한다.
RippleNet 학습에 필요한 엔티티/관계 인덱스 매핑도 관리한다.
"""
from __future__ import annotations

import pickle
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import networkx as nx

# ── 데이터클래스 ──────────────────────────────────────────────────────────────


@dataclass
class RippleTriple:
    """RippleNet 학습/추론에 사용되는 (head_idx, relation_idx, tail_idx) 정수 트리플."""
    head_idx: int
    relation_idx: int
    tail_idx: int
    confidence: float = 1.0


# ── 추상 KGStore ──────────────────────────────────────────────────────────────


class KGStore(ABC):
    """지식 그래프 저장소 인터페이스."""

    @abstractmethod
    def add_node(self, node_id: str, node_type: str, **attrs: Any) -> None:
        ...

    @abstractmethod
    def add_edge(
        self,
        src: str,
        dst: str,
        relation: str,
        confidence: float = 1.0,
        **attrs: Any,
    ) -> None:
        ...

    @abstractmethod
    def get_node(self, node_id: str) -> dict[str, Any] | None:
        ...

    @abstractmethod
    def get_neighbors(
        self,
        node_id: str,
        relation: str | None = None,
        min_confidence: float = 0.0,
    ) -> list[tuple[str, str, float]]:
        """(neighbor_id, relation, confidence) 목록 반환."""
        ...

    @abstractmethod
    def get_ripple_set(
        self,
        seed_ids: list[str],
        hop: int,
        n_memory: int = 32,
    ) -> list[tuple[str, str, str]]:
        """(head_id, relation, tail_id) 튜플 목록 반환 (ripple set at given hop)."""
        ...

    @abstractmethod
    def find_paths(
        self,
        src_id: str,
        dst_id: str,
        max_hops: int = 3,
    ) -> list[list[str]]:
        """src → dst 경로(노드 ID 리스트) 목록 반환."""
        ...

    @abstractmethod
    def all_entity_ids(self) -> list[str]:
        ...

    @abstractmethod
    def all_relations(self) -> list[str]:
        ...

    @abstractmethod
    def node_count(self) -> int:
        ...

    @abstractmethod
    def edge_count(self) -> int:
        ...

    # ── 공통 인덱스 관리 ────────────────────────────────────────────────────

    def build_index(self) -> tuple[dict[str, int], dict[str, int]]:
        """엔티티/관계 → 정수 인덱스 매핑을 생성한다 (RippleNet 학습용)."""
        entity_ids = self.all_entity_ids()
        relation_names = self.all_relations()

        entity2idx: dict[str, int] = {eid: i for i, eid in enumerate(entity_ids)}
        relation2idx: dict[str, int] = {rel: i for i, rel in enumerate(relation_names)}
        return entity2idx, relation2idx

    def get_ripple_set_indexed(
        self,
        seed_ids: list[str],
        hop: int,
        entity2idx: dict[str, int],
        relation2idx: dict[str, int],
        n_memory: int = 32,
    ) -> list[RippleTriple]:
        """RippleNet 용 정수 인덱스 기반 ripple set."""
        raw_triples = self.get_ripple_set(seed_ids, hop, n_memory)
        result: list[RippleTriple] = []
        for head_id, rel, tail_id in raw_triples:
            h = entity2idx.get(head_id)
            r = relation2idx.get(rel)
            t = entity2idx.get(tail_id)
            if h is not None and r is not None and t is not None:
                result.append(RippleTriple(head_idx=h, relation_idx=r, tail_idx=t))
        return result


# ── NetworkX 구현 ─────────────────────────────────────────────────────────────


class NetworkXKGStore(KGStore):
    """인메모리 NetworkX 기반 KG 저장소."""

    def __init__(self) -> None:
        self.graph: nx.MultiDiGraph = nx.MultiDiGraph()
        self._entity_ids: list[str] = []
        self._relations: set[str] = set()

    def add_node(self, node_id: str, node_type: str, **attrs: Any) -> None:
        if node_id not in self.graph:
            self._entity_ids.append(node_id)
        self.graph.add_node(node_id, type=node_type, **attrs)

    def add_edge(
        self,
        src: str,
        dst: str,
        relation: str,
        confidence: float = 1.0,
        **attrs: Any,
    ) -> None:
        # 노드가 없으면 기본 타입으로 자동 생성
        if src not in self.graph:
            self.add_node(src, node_type="Unknown", label=src)
        if dst not in self.graph:
            self.add_node(dst, node_type="Unknown", label=dst)
        self.graph.add_edge(src, dst, relation=relation, confidence=confidence, **attrs)
        self._relations.add(relation)

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        if node_id not in self.graph:
            return None
        return dict(self.graph.nodes[node_id])

    def get_neighbors(
        self,
        node_id: str,
        relation: str | None = None,
        min_confidence: float = 0.0,
    ) -> list[tuple[str, str, float]]:
        if node_id not in self.graph:
            return []
        results: list[tuple[str, str, float]] = []
        for _, neighbor, edge_data in self.graph.out_edges(node_id, data=True):
            rel = edge_data.get("relation", "")
            conf = edge_data.get("confidence", 1.0)
            if conf < min_confidence:
                continue
            if relation is not None and rel != relation:
                continue
            results.append((neighbor, rel, conf))
        return results

    def get_ripple_set(
        self,
        seed_ids: list[str],
        hop: int,
        n_memory: int = 32,
    ) -> list[tuple[str, str, str]]:
        """hop 번째 ripple set: seed 로부터 정확히 hop 번 이동한 (head, relation, tail) 트리플."""
        if hop == 0:
            # hop 0 = seed 자체와 연결된 1-hop 이웃
            current_nodes = set(seed_ids)
        else:
            # hop h = (h-1)-hop ripple set 의 tail 집합
            prev_ripple = self.get_ripple_set(seed_ids, hop - 1, n_memory * 2)
            current_nodes = {t for _, _, t in prev_ripple}

        triples: list[tuple[str, str, str]] = []
        seen_tails: set[str] = set()

        for head_id in current_nodes:
            if head_id not in self.graph:
                continue
            for _, tail_id, edge_data in self.graph.out_edges(head_id, data=True):
                rel = edge_data.get("relation", "RELATED_TO")
                triples.append((head_id, rel, tail_id))
                seen_tails.add(tail_id)

        # n_memory 개로 제한 (confidence 내림차순)
        triples.sort(
            key=lambda t: self.graph.get_edge_data(t[0], t[2], default={}).get("confidence", 0.5),
            reverse=True,
        )
        return triples[:n_memory]

    def find_paths(
        self,
        src_id: str,
        dst_id: str,
        max_hops: int = 3,
    ) -> list[list[str]]:
        """BFS 로 src → dst 사이 최단 경로들을 탐색한다."""
        if src_id not in self.graph or dst_id not in self.graph:
            return []

        paths: list[list[str]] = []
        queue: deque[list[str]] = deque([[src_id]])

        while queue:
            path = queue.popleft()
            if len(path) > max_hops + 1:
                break
            current = path[-1]
            if current == dst_id:
                paths.append(path)
                if len(paths) >= 5:
                    break
                continue
            for _, neighbor, _ in self.graph.out_edges(current, data=True):
                if neighbor not in path:
                    queue.append(path + [neighbor])

        return paths

    def find_explanation_path(
        self,
        src_id: str,
        dst_id: str,
        max_hops: int = 3,
    ) -> list[tuple[str, str, str]]:
        """(head, relation, tail) 튜플 형태의 설명 경로를 반환한다."""
        paths = self.find_paths(src_id, dst_id, max_hops)
        if not paths:
            return []

        path = paths[0]
        result: list[tuple[str, str, str]] = []
        for i in range(len(path) - 1):
            head = path[i]
            tail = path[i + 1]
            edge_data = self.graph.get_edge_data(head, tail)
            if edge_data:
                first_key = list(edge_data.keys())[0]
                rel = edge_data[first_key].get("relation", "RELATED_TO")
            else:
                rel = "RELATED_TO"
            head_label = self.graph.nodes[head].get("label", head)
            tail_label = self.graph.nodes[tail].get("label", tail)
            result.append((head_label, rel, tail_label))
        return result

    def all_entity_ids(self) -> list[str]:
        return list(self.graph.nodes())

    def all_relations(self) -> list[str]:
        return sorted(self._relations)

    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def get_book_ids(self) -> list[str]:
        """Book 타입 노드 ID 목록을 반환한다."""
        return [
            nid for nid, data in self.graph.nodes(data=True)
            if data.get("type") == "Book"
        ]

    def get_label(self, node_id: str) -> str:
        """노드 레이블을 반환한다."""
        node_data = self.graph.nodes.get(node_id, {})
        return node_data.get("label", node_id)

    def summary(self) -> str:
        return f"NetworkX KG: 노드 {self.node_count()}개, 엣지 {self.edge_count()}개"

    def save(self, path: str | Path) -> None:
        """KG 를 파일로 직렬화한다."""
        with open(path, "wb") as f:
            pickle.dump({
                "graph": self.graph,
                "entity_ids": self._entity_ids,
                "relations": self._relations,
            }, f)

    @classmethod
    def load(cls, path: str | Path) -> "NetworkXKGStore":
        """파일에서 KG 를 복원한다."""
        store = cls()
        with open(path, "rb") as f:
            data = pickle.load(f)
        store.graph = data["graph"]
        store._entity_ids = data["entity_ids"]
        store._relations = data["relations"]
        return store


# ── Neo4j 구현 (선택적) ───────────────────────────────────────────────────────


class Neo4jKGStore(KGStore):
    """Neo4j 기반 KG 저장소. `pip install neo4j` 필요."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        try:
            from neo4j import GraphDatabase  # type: ignore[import]
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            self._available = True
            print(f"[INFO] Neo4j 연결 성공: {uri}")
        except ImportError:
            raise RuntimeError("neo4j 패키지가 설치되지 않았습니다. pip install neo4j")
        except Exception as e:
            raise RuntimeError(f"Neo4j 연결 실패: {e}")

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    def add_node(self, node_id: str, node_type: str, **attrs: Any) -> None:
        props = {"node_id": node_id, **attrs}
        query = (
            f"MERGE (n:{node_type} {{node_id: $node_id}}) "
            "SET n += $props"
        )
        with self._driver.session() as session:
            session.run(query, node_id=node_id, props=props)

    def add_edge(
        self,
        src: str,
        dst: str,
        relation: str,
        confidence: float = 1.0,
        **attrs: Any,
    ) -> None:
        query = (
            "MATCH (a {node_id: $src}), (b {node_id: $dst}) "
            f"MERGE (a)-[r:{relation}]->(b) "
            "SET r.confidence = $confidence, r += $attrs"
        )
        with self._driver.session() as session:
            session.run(query, src=src, dst=dst, confidence=confidence, attrs=attrs)

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        with self._driver.session() as session:
            result = session.run(
                "MATCH (n {node_id: $node_id}) RETURN n", node_id=node_id
            )
            record = result.single()
            return dict(record["n"]) if record else None

    def get_neighbors(
        self,
        node_id: str,
        relation: str | None = None,
        min_confidence: float = 0.0,
    ) -> list[tuple[str, str, float]]:
        rel_filter = f"[r:{relation}]" if relation else "[r]"
        query = (
            f"MATCH (a {{node_id: $node_id}})-{rel_filter}->(b) "
            "WHERE r.confidence >= $min_conf "
            "RETURN b.node_id AS neighbor, type(r) AS rel, r.confidence AS conf"
        )
        with self._driver.session() as session:
            result = session.run(query, node_id=node_id, min_conf=min_confidence)
            return [(r["neighbor"], r["rel"], r["conf"]) for r in result]

    def get_ripple_set(
        self,
        seed_ids: list[str],
        hop: int,
        n_memory: int = 32,
    ) -> list[tuple[str, str, str]]:
        depth = hop + 1
        query = (
            "MATCH (seed)-[*" + str(depth) + "]->(tail) "
            "WHERE seed.node_id IN $seed_ids "
            "MATCH (head)-[r]->(tail) "
            "RETURN head.node_id AS h, type(r) AS rel, tail.node_id AS t, "
            "r.confidence AS conf "
            "ORDER BY conf DESC LIMIT $n_memory"
        )
        with self._driver.session() as session:
            result = session.run(query, seed_ids=seed_ids, n_memory=n_memory)
            return [(r["h"], r["rel"], r["t"]) for r in result]

    def find_paths(
        self,
        src_id: str,
        dst_id: str,
        max_hops: int = 3,
    ) -> list[list[str]]:
        query = (
            "MATCH p = shortestPath((a {node_id: $src})-[*1.." + str(max_hops) + "]->(b {node_id: $dst})) "
            "RETURN [node IN nodes(p) | node.node_id] AS path"
        )
        with self._driver.session() as session:
            result = session.run(query, src=src_id, dst=dst_id)
            return [r["path"] for r in result]

    def all_entity_ids(self) -> list[str]:
        with self._driver.session() as session:
            result = session.run("MATCH (n) RETURN n.node_id AS id")
            return [r["id"] for r in result if r["id"]]

    def all_relations(self) -> list[str]:
        with self._driver.session() as session:
            result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
            return [r["relationshipType"] for r in result]

    def node_count(self) -> int:
        with self._driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS cnt")
            return result.single()["cnt"]

    def edge_count(self) -> int:
        with self._driver.session() as session:
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt")
            return result.single()["cnt"]

    def summary(self) -> str:
        return f"Neo4j KG: 노드 {self.node_count()}개, 엣지 {self.edge_count()}개"


# ── 팩토리 함수 ───────────────────────────────────────────────────────────────


def create_kg_store(
    backend: str = "networkx",
    neo4j_uri: str = "",
    neo4j_user: str = "",
    neo4j_password: str = "",
) -> KGStore:
    """KG 저장소를 생성한다. Neo4j 가 실패하면 NetworkX 로 폴백."""
    if backend == "neo4j" and neo4j_uri:
        try:
            return Neo4jKGStore(neo4j_uri, neo4j_user, neo4j_password)
        except Exception as e:
            print(f"[WARN] Neo4j 초기화 실패, NetworkX 로 폴백합니다: {e}")
    return NetworkXKGStore()
