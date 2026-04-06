import json
import os
import networkx as nx
from pyvis.network import Network


class GraphExtractor:
    """Builds and visualizes a directed knowledge graph from subject-predicate-object triplets."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.graph = nx.DiGraph()

    def load_json(self, filename: str = "graph.json") -> bool:
        """Load an existing graph from JSON. Returns True if file found."""
        path = os.path.join(self.output_dir, filename)
        if not os.path.exists(path):
            return False
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        edge_key = "links" if "links" in data else "edges"
        self.graph = nx.node_link_graph(data, edges=edge_key)
        return True

    def add_triplet(self, subject: str, predicate: str, object_node: str) -> None:
        """Add a single subject-predicate-object relationship to the graph."""
        self.graph.add_edge(subject, object_node, label=predicate)

    def save_json(self, filename: str = "graph.json") -> None:
        """Persist graph to JSON using node-link format."""
        data = nx.node_link_data(self.graph, edges="links")
        with open(os.path.join(self.output_dir, filename), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def generate_visualization(self, filename: str = "graph.html") -> str:
        """Generate an interactive HTML visualization with PyVis."""
        net = Network(
            height="750px",
            width="100%",
            bgcolor="#222222",
            font_color="white",
            directed=True,
        )
        for node in self.graph.nodes():
            net.add_node(node, label=node, title=node)
        for source, target, data in self.graph.edges(data=True):
            net.add_edge(source, target, label=data.get("label", ""))
        path = os.path.join(self.output_dir, filename)
        net.save_graph(path)
        return path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python graph_extractor.py <output_dir> <triplets_json>")
        sys.exit(1)

    folder = sys.argv[1]
    triplets_file = sys.argv[2]

    extractor = GraphExtractor(folder)
    extractor.load_json()  # merge with existing graph if present

    with open(triplets_file, "r", encoding="utf-8") as f:
        triplets = json.load(f)

    for t in triplets:
        extractor.add_triplet(t["subject"], t["predicate"], t["object"])

    extractor.save_json()
    html_path = extractor.generate_visualization()
    print(f"Graph saved to {folder}")
    print(f"Visualization: {html_path}")
