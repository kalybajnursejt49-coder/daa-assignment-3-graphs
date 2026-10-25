import json
import pathlib
import sys

root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "tools"))
sys.path.insert(0, str(root / "src" / "Python"))

from public_validate import check
from algorithms import dag, reconstruct_route


def read(name):
    return [json.loads(line) for line in (root / "tests" / name).read_text(encoding="utf-8").splitlines()]


inputs = read("own_cases.jsonl")
expected = read("expected.jsonl")
actual = read("actual.jsonl")
assert len(inputs) == len(expected) == len(actual)
for request, target, result in zip(inputs, expected, actual):
    assert check(request, result, target), (request, result)

forest = inputs[3]
forest_target = expected[3]
assert check(forest, {"cost": 1000000001, "components": 2, "edge_ids": [5, 3, 1]}, forest_target)
assert not check(forest, {"cost": 999999901, "components": 2, "edge_ids": [4, 1, 5]}, forest_target)

scc_request = inputs[5]
scc_target = expected[5]
assert check(scc_request, {"component": [8, 8, 4, 4, 9, 12], "condensation": [[8, 4], [4, 9]]}, scc_target)
assert not check(scc_request, {"component": [8, 8, 4, 4, 9, 12], "condensation": [[8, 4]]}, scc_target)

topo_request = inputs[6]
topo_target = expected[6]
assert check(topo_request, {"acyclic": True, "order": [1, 0, 2, 3]}, topo_target)
assert not check(topo_request, {"acyclic": True, "order": [2, 0, 1, 3]}, topo_target)

dag_request = inputs[8]
dag_target = expected[8]
assert check(dag_request, {"acyclic": True, "distance": [0, 4, -1, 2, None, None], "parent_edge": [-1, 1, 2, 4, -1, -1]}, dag_target)
assert not check(dag_request, {"acyclic": True, "distance": [0, 4, -1, 2, None, None], "parent_edge": [-1, 0, 3, 4, -1, -1]}, dag_target)

result = dag(dag_request)
parents = result["parent_edge"]
edges = dag_request["edges"]
assert reconstruct_route(0, 3, parents, edges) == [0, 1, 2, 3]
assert reconstruct_route(0, 0, parents, edges) == [0]
assert reconstruct_route(0, 5, parents, edges) == []
assert reconstruct_route(0, 1, [-1, 1, 2, 4, -1, -1], edges) == [0, 1]
print(f"PASS {len(inputs)} own cases, four witness alternatives, four route calls")
