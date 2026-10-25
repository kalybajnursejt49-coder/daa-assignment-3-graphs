import gc
import json
import pathlib
import platform
import random
import statistics
import sys
import time

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src" / "Python"))
sys.path.insert(0, str(root / "tools"))

import algorithms
from public_validate import check


def forest_valid(request, answer):
    return check(request, answer, {"cost": answer["cost"], "components": 1})


def large_tests():
    n = 100000
    m = 250000
    report = {}
    operations = [[i % (n - 1), i % (n - 1) + 1] for i in range(m)]
    result = algorithms.dsu({"n": n, "operations": operations})
    assert len(result["states"]) == m and result["states"][-1] == [1, n]
    report["dsu"] = {"n": n, "operations": m, "final": result["states"][-1]}
    del operations, result
    gc.collect()

    weighted = [[i, i + 1, 1] for i in range(n - 1)]
    weighted.extend([[i % (n - 1), i % (n - 1) + 1, 2] for i in range(m - n + 1)])
    for name in ("kruskal", "prim"):
        request = {"task": name, "n": n, "edges": weighted}
        result = getattr(algorithms, name)(request)
        assert result["cost"] == n - 1 and forest_valid(request, result)
        report[name] = {"n": n, "m": m, "cost": result["cost"], "selected": len(result["edge_ids"])}
    del weighted, result
    gc.collect()

    directed = [[i, i + 1] for i in range(n - 1)]
    directed.extend([[i % (n - 1), i % (n - 1) + 1] for i in range(m - n + 1)])
    result = algorithms.scc({"n": n, "edges": directed})
    assert len(set(result["component"])) == n and len(result["condensation"]) == n - 1
    report["scc"] = {"n": n, "m": m, "components": n, "condensation_edges": n - 1}
    result = algorithms.topo({"n": n, "edges": directed})
    assert result["acyclic"] and result["order"] == list(range(n))
    report["topo"] = {"n": n, "m": m, "first": result["order"][0], "last": result["order"][-1]}
    del directed, result
    gc.collect()

    dag_edges = [[i, i + 1, -1] for i in range(n - 1)]
    dag_edges.extend([[i % (n - 1), i % (n - 1) + 1, 1] for i in range(m - n + 1)])
    result = algorithms.dag({"n": n, "source": 0, "edges": dag_edges})
    assert result["acyclic"] and result["distance"][-1] == -(n - 1)
    assert len(algorithms.reconstruct_route(0, n - 1, result["parent_edge"], dag_edges)) == n
    report["dag"] = {"n": n, "m": m, "last_distance": result["distance"][-1], "route_vertices": n}
    return report


def make_graph(n, m, seed):
    rng = random.Random(seed)
    edges = [[i, i + 1, rng.randint(-1000000, 1000000)] for i in range(n - 1)]
    while len(edges) < m:
        a = rng.randrange(n)
        b = rng.randrange(n)
        edges.append([a, b, rng.randint(-1000000, 1000000)])
    return edges


def benchmarks():
    rows = []
    for n, m, seed in ((1000, 4000, 314159), (5000, 20000, 314160), (20000, 80000, 314161)):
        edges = make_graph(n, m, seed)
        requests = {name: {"task": name, "n": n, "edges": edges} for name in ("kruskal", "prim")}
        results = {name: getattr(algorithms, name)(requests[name]) for name in requests}
        assert results["kruskal"]["cost"] == results["prim"]["cost"]
        assert all(forest_valid(requests[name], results[name]) for name in requests)
        for name in requests:
            getattr(algorithms, name)(requests[name])
        times = {name: [] for name in requests}
        for repeat in range(3):
            for name in (("kruskal", "prim") if repeat % 2 == 0 else ("prim", "kruskal")):
                start = time.perf_counter_ns()
                result = getattr(algorithms, name)(requests[name])
                elapsed = (time.perf_counter_ns() - start) / 1000000
                assert result["cost"] == results[name]["cost"]
                times[name].append(round(elapsed, 3))
        rows.append({"n": n, "m": m, "seed": seed, "cost": results["kruskal"]["cost"],
                     "kruskal_ms": times["kruskal"], "prim_ms": times["prim"],
                     "kruskal_median_ms": round(statistics.median(times["kruskal"]), 3),
                     "prim_median_ms": round(statistics.median(times["prim"]), 3)})
    return rows


output = {"python": platform.python_version(), "platform": platform.platform(),
          "processor": platform.processor(), "scale": large_tests(), "benchmark": benchmarks()}
(root / "tests" / "scale_benchmark_actual.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
print(json.dumps(output, indent=2))
