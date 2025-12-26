from heapq import heappush, heappop

def astar(graph, start, goal, penalty, positions):

    end_pos = positions[goal]
    x2 = end_pos[0]
    y2 = end_pos[1]

    def h(n):
        n_pos = positions[n]
        x1 = n_pos[0]
        y1 = n_pos[1]
        map_dist = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        distance_est = map_dist * 0.7
        return (distance_est / 34) * 60

    open_list = []
    heappush(open_list, (h(start), start))
    prev_node = {}
    g = {start: 0}
    used_lines = set()

    while open_list:
        f, current = heappop(open_list)

        if current == goal:
            path = [current]
            while current in prev_node:
                current = prev_node[current]
                path.append(current)
            path.reverse()
            return path, g[goal]

        for neighbor, data in graph[current].items():
            g_new = g[current] + data["weight"]

            if current != start:
                prev = prev_node[current]
                prev_line = graph[prev][current]["line"]
                if data["line"] != prev_line:
                    g_new += penalty

            if neighbor not in g or g_new < g[neighbor]:
                g[neighbor] = g_new
                f = g_new + h(neighbor)
                heappush(open_list, (f, neighbor))
                prev_node[neighbor] = current

    return [], 0
