"""Small deterministic K-means grouping for comparable material barrier data."""

from dataclasses import dataclass
from math import log
from typing import List

from src.rule_engine.models import Material


@dataclass
class ClusteredMaterials:
    materials: List[Material]
    cluster_by_material: List[int | None]
    clustered_count: int
    unclustered_count: int
    cluster_count: int
    explanation: str


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def group_materials(materials: List[Material], n_clusters: int = 4) -> ClusteredMaterials:
    """Cluster log10 OTR/WVTR pairs, then retain incomplete records unclustered.

    Missing values are never imputed. Values must already be canonical or converted
    by the existing unit normalizer. Cluster IDs are stable for a stable input list.
    """
    comparable = [
        material for material in materials
        if material.otr_cm3_m2_day is not None
        and material.wvtr_g_m2_day is not None
        and material.otr_cm3_m2_day > 0
        and material.wvtr_g_m2_day > 0
        and material.otr_status in ("CANONICAL", "CONVERTED")
        and material.wvtr_status in ("CANONICAL", "CONVERTED")
    ]
    unclustered = [material for material in materials if material not in comparable]
    if not comparable:
        return ClusteredMaterials(materials, [None] * len(materials), 0, len(unclustered), 0,
            "No materials have comparable positive OTR and WVTR values; rule evaluation used all records without clustering.")

    points = [(log(m.otr_cm3_m2_day, 10), log(m.wvtr_g_m2_day, 10)) for m in comparable]
    k = max(1, min(int(n_clusters), len(points)))
    # Deterministic quantile seeds avoid a random dependency and stabilize the MVP.
    ordered = sorted(range(len(points)), key=lambda i: (points[i][0], points[i][1], i))
    centers = [points[ordered[min(len(ordered)-1, int((j + 0.5) * len(ordered) / k))]] for j in range(k)]
    labels = [0] * len(points)
    for _ in range(100):
        updated_labels = [min(range(k), key=lambda c: (_distance(point, centers[c]), c)) for point in points]
        updated_centers = []
        for c in range(k):
            members = [points[i] for i, label in enumerate(updated_labels) if label == c]
            updated_centers.append((
                sum(p[0] for p in members) / len(members),
                sum(p[1] for p in members) / len(members),
            ) if members else centers[c])
        if updated_labels == labels and updated_centers == centers:
            break
        labels, centers = updated_labels, updated_centers

    labels_by_object = {id(material): label for material, label in zip(comparable, labels)}
    mapping = [labels_by_object.get(id(material)) for material in materials]
    return ClusteredMaterials(
        materials=materials,
        cluster_by_material=mapping,
        clustered_count=len(comparable),
        unclustered_count=len(unclustered),
        cluster_count=k,
        explanation=(f"Grouped {len(comparable)} materials with comparable OTR and WVTR values into {k} clusters using log10 barrier values. "
                     f"{len(unclustered)} incomplete or non-positive records were left unclustered and retained for rule review. "
                     "Clusters only organize candidates; they do not select or exclude materials. Hard rules determine the final status."),
    )
