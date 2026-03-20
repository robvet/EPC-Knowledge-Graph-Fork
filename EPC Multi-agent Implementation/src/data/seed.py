"""Master seed script — populates the graph with a complete sample project."""

from __future__ import annotations

from src.graph.client import GraphClient, get_graph
from src.graph.models import Industry, Project, ProjectStatus
from src.data.sources import primavera_p6, sap_mm, aconex, smartplant, o3_awp


PROJECT_ID = "PRJ-001"


def seed(graph: GraphClient | None = None) -> GraphClient:
    """Seed **LNG Train 4** into *graph*.

    Returns the populated graph client.
    """
    g = graph or get_graph()
    g.clear()

    # Root project vertex
    project = Project(
        id=PROJECT_ID,
        name="LNG Train 4",
        client="Worley / TotalEnergies JV",
        status=ProjectStatus.ACTIVE,
        budget=285_000_000.0,
        currency="USD",
        location="Ras Laffan Industrial City",
        country="Qatar",
        industry=Industry.CONVENTIONAL_ENERGY,
    )
    g.add_vertex("Project", project)

    # Ingest from each data source
    primavera_p6.ingest(g, PROJECT_ID)
    sap_mm.ingest(g, PROJECT_ID)
    aconex.ingest(g, PROJECT_ID)
    smartplant.ingest(g, PROJECT_ID)
    o3_awp.ingest(g, PROJECT_ID)

    return g


if __name__ == "__main__":
    g = seed()
    print(f"Graph seeded: {g.vertex_count()} vertices, {g.edge_count()} edges")
    print("Summary:", g.summary())
