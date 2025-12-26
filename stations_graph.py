import networkx as nx


def data_graph(data):
    graph = nx.Graph()
    positions = {}
    label_pos = {}
    elevators = {}
    line_colors = {}

    for name, info in data["stations"].items():
        graph.add_node(name)
        positions[name] = tuple(info["coords"])
        label_pos[name] = tuple(info["label"])
        elevators[name] = info["elevator"]

        for neighbor in info["connections"]:
            to = neighbor["to"]
            graph.add_edge(name, to, line=neighbor["line"], weight=neighbor["distance"])

            color = data["lines"][neighbor["line"]]
            if color not in line_colors:
                line_colors[color] = []
            line_colors[color].append((name, to))

    return graph, positions, label_pos, elevators, line_colors
