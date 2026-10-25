import heapq


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n
        self.largest = int(n > 0)

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        a = self.find(a)
        b = self.find(b)
        if a == b:
            return False
        if self.size[a] < self.size[b]:
            a, b = b, a
        self.parent[b] = a
        self.size[a] += self.size[b]
        self.components -= 1
        self.largest = max(self.largest, self.size[a])
        return True


def dsu(request):
    uf = UnionFind(request["n"])
    states = []
    for a, b in request["operations"]:
        uf.union(a, b)
        states.append([uf.components, uf.largest])
    return {"states": states}


def kruskal(request):
    edges = request["edges"]
    uf = UnionFind(request["n"])
    chosen = []
    cost = 0
    for i in sorted(range(len(edges)), key=lambda i: (edges[i][2], i)):
        a, b, weight = edges[i]
        if uf.union(a, b):
            chosen.append(i)
            cost += weight
    return {"cost": cost, "edge_ids": chosen, "components": uf.components}


def prim(request):
    n = request["n"]
    graph = [[] for _ in range(n)]
    for i, (a, b, weight) in enumerate(request["edges"]):
        graph[a].append((weight, i, b))
        graph[b].append((weight, i, a))
    seen = [False] * n
    chosen = []
    cost = 0
    components = 0
    for start in range(n):
        if seen[start]:
            continue
        components += 1
        seen[start] = True
        heap = list(graph[start])
        heapq.heapify(heap)
        while heap:
            weight, i, vertex = heapq.heappop(heap)
            if seen[vertex]:
                continue
            seen[vertex] = True
            chosen.append(i)
            cost += weight
            for item in graph[vertex]:
                if not seen[item[2]]:
                    heapq.heappush(heap, item)
    return {"cost": cost, "edge_ids": chosen, "components": components}


def scc(request):
    n = request["n"]
    edges = request["edges"]
    graph = [[] for _ in range(n)]
    reverse = [[] for _ in range(n)]
    for a, b in edges:
        graph[a].append(b)
        reverse[b].append(a)
    seen = [False] * n
    finish = []
    for start in range(n):
        if seen[start]:
            continue
        seen[start] = True
        stack = [(start, 0)]
        while stack:
            vertex, index = stack[-1]
            if index == len(graph[vertex]):
                finish.append(vertex)
                stack.pop()
                continue
            stack[-1] = (vertex, index + 1)
            next_vertex = graph[vertex][index]
            if not seen[next_vertex]:
                seen[next_vertex] = True
                stack.append((next_vertex, 0))
    component = [-1] * n
    count = 0
    for start in reversed(finish):
        if component[start] != -1:
            continue
        component[start] = count
        stack = [start]
        while stack:
            vertex = stack.pop()
            for next_vertex in reverse[vertex]:
                if component[next_vertex] == -1:
                    component[next_vertex] = count
                    stack.append(next_vertex)
        count += 1
    pairs = {(component[a], component[b]) for a, b in edges if component[a] != component[b]}
    return {"component": component, "condensation": [list(pair) for pair in sorted(pairs)]}


def topological_order(graph):
    state = [0] * len(graph)
    order = []
    for start in range(len(graph)):
        if state[start]:
            continue
        state[start] = 1
        stack = [(start, 0)]
        while stack:
            vertex, index = stack[-1]
            if index == len(graph[vertex]):
                state[vertex] = 2
                order.append(vertex)
                stack.pop()
                continue
            stack[-1] = (vertex, index + 1)
            next_vertex = graph[vertex][index]
            if state[next_vertex] == 1:
                return None
            if state[next_vertex] == 0:
                state[next_vertex] = 1
                stack.append((next_vertex, 0))
    order.reverse()
    return order


def topo(request):
    graph = [[] for _ in range(request["n"])]
    for a, b in request["edges"]:
        graph[a].append(b)
    order = topological_order(graph)
    return {"acyclic": order is not None, "order": order if order is not None else []}


def dag(request):
    n = request["n"]
    edges = request["edges"]
    graph = [[] for _ in range(n)]
    for a, b, weight in edges:
        graph[a].append(b)
    order = topological_order(graph)
    if order is None:
        return {"acyclic": False, "distance": [], "parent_edge": []}
    outgoing = [[] for _ in range(n)]
    for i, (a, b, weight) in enumerate(edges):
        outgoing[a].append((b, weight, i))
    distance = [None] * n
    parent_edge = [-1] * n
    distance[request["source"]] = 0
    for vertex in order:
        if distance[vertex] is None:
            continue
        for next_vertex, weight, i in outgoing[vertex]:
            candidate = distance[vertex] + weight
            if distance[next_vertex] is None or candidate < distance[next_vertex]:
                distance[next_vertex] = candidate
                parent_edge[next_vertex] = i
    return {"acyclic": True, "distance": distance, "parent_edge": parent_edge}


def reconstruct_route(source, target, parent_edge, edges):
    route = [target]
    while route[-1] != source:
        edge_id = parent_edge[route[-1]]
        if edge_id == -1:
            return []
        route.append(edges[edge_id][0])
    route.reverse()
    return route
