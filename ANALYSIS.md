# Assignment 3 analysis

## Build, run and test

Selected language: Python. Python 3.12 or newer is required. There is no compilation or external package installation.

From the repository root:

```sh
python tools/run.py --setup
python tools/run.py --check
python tools/run.py --input tests/own_cases.jsonl
python tools/run.py --input tests/own_cases.jsonl > tests/actual.jsonl
python tests/check_own.py
python tests/scale_benchmark.py
```

The launcher reads UTF-8 JSON Lines and writes one compact JSON result per request. `ping` stays in the supplied entry point. Every algorithm creates its own arrays, sets and heap for the current request; no result depends on a previous line. The public checker sends two complete batches through one process. The algorithms use loops and explicit DFS stacks, so chains of 100,000 vertices do not depend on the Python recursion limit.

## DSU

Each vertex starts as its own set. `find` follows parents to a root and compresses the path by halving. `union` attaches the smaller root to the larger root, decreases the component count and updates the largest size only when roots differ. After every operation, the root size is the size of its set; the component count equals the number of roots. Since an operation only joins two distinct sets, these values are correct after every pair. A self-union or repeated pair leaves them unchanged. For `n=0`, the state list is empty.

Time: `O(n + q α(n))` amortized. Space: `O(n + q)`, including the returned states.

## Kruskal

Sort original edge IDs by weight, keeping their input positions. Process each edge in order and select it only if its endpoints have different DSU roots. At every step the selected edges form a forest. The cut property permits a minimum-weight edge connecting two current sets in an optimal spanning forest, so every selection is safe. When all edges have been processed, each input component has been spanned. The remaining DSU count includes isolated vertices. Loops have equal roots and are skipped; parallel and negative edges need no special rule.

Time: `O(n + m log(m+1))`. Space: `O(n+m)`. Python integer costs also cover sums beyond 32 bits.

## Prim

Build undirected adjacency lists with original edge IDs. Start at every vertex that has not yet been visited. Mark it, then repeatedly take the cheapest heap edge whose destination is still unvisited. The visited vertices in one run form a tree, and the heap contains crossing candidates. By the cut property, the cheapest crossing edge is safe. A new start is needed exactly once per input component, including isolates. Loops lead to already visited vertices and are ignored. Parallel, tied and negative edges remain valid heap candidates.

Time: `O(n + m log(m+1))` with a lazy heap. Space: `O(n+m)`.

## SCC

Build the directed graph and its transpose. The first iterative DFS records vertices when all outgoing edges have been examined. The second DFS visits the transpose in reverse finishing order and assigns one label per traversal. Its invariant is that a second-pass traversal reaches exactly the remaining vertices in one strongly connected component: the finish order prevents it from entering another unassigned component. A set of pairs from input edges produces the condensation edges, excluding internal and duplicate pairs. Isolates receive separate labels; loops remain internal.

Time: `O(n+m)` expected, using a hash set for pair deduplication. Space: `O(n+m)`.

## Topological ordering

DFS has states 0 (unvisited), 1 (active) and 2 (finished). The explicit stack stores the next neighbor index for every suspended vertex. An edge to state 1 closes a directed cycle. If no such edge exists, every edge leads from an earlier to a later vertex in reversed finish order. The DFS starts at every unvisited vertex, so cycles in disconnected parts are found as well. A self-loop is an active-state edge. Empty graphs produce an empty valid order.

Time: `O(n+m)`. Space: `O(n+m)` including the output order and adjacency lists.

## DAG shortest paths and route reconstruction

Run the same three-state DFS over the entire graph first. Any cycle, even one unreachable from `source`, returns empty arrays. Otherwise set the source distance to zero, all other distances to `null`, and scan vertices in topological order. Relax outgoing edges only from vertices with finite distances. Before a vertex is scanned, all paths ending there have already been considered because every incoming edge starts earlier in the order. Thus its distance is shortest, including with negative weights. A successful relaxation stores the original incoming edge ID; ties keep the first optimal parent. Unreachable vertices remain `null` and `-1`. The helper follows those parent edge IDs backward and reverses the collected vertices; it returns `[]` when no parent leads to the source.

Time: `O(n+m)` for the algorithm, `O(L)` for a route with `L` vertices. Space: `O(n+m)` for the algorithm and `O(L)` output space for the helper.

Actual helper calls in `tests/check_own.py` use the DAG input on line 9 of `tests/own_cases.jsonl`:

| Call | Result | Selected edge IDs and total weight |
| --- | --- | --- |
| `reconstruct_route(0, 3, parents, edges)` | `[0,1,2,3]` | `[0,2,4]`, `4-5+3=2` |
| `reconstruct_route(0, 0, parents, edges)` | `[0]` | `[]`, `0` |
| `reconstruct_route(0, 5, parents, edges)` | `[]` | No route; `distance[5]=null` |
| `reconstruct_route(0, 1, [-1,1,2,4,-1,-1], edges)` | `[0,1]` | `[1]`, `4`; parallel edge 1 ties edge 0 |

## Own tests

`tests/own_cases.jsonl`, `tests/expected.jsonl` and `tests/actual.jsonl` contain requests, justified expected values and actual output in matching line order. Lines 2-3 cover empty and repeated DSU unions. Lines 4-5 cover negative and parallel edges, a loop, ties and an isolated component. Line 6 covers SCC duplicates, a loop and an isolate. Lines 7-8 cover valid precedence and a disconnected cycle. Lines 9-10 cover negative DAG distance, unreachable vertices, parallel ties and a cycle unreachable from the source. Lines 11-12 cover 64-bit totals.

`tests/check_own.py` compares semantic validity using the supplied public witness validator, rather than requiring exact IDs, SCC labels, topological order or tied parents. It also checks an alternative valid answer and an invalid witness for each non-unique result type. For example, the forest may use IDs `[5,3,1]` instead of `[1,2,5]`; selecting loop ID `4` is invalid. The SCC may use labels `[8,8,4,4,9,12]`; omitting the condensation pair `[4,9]` is invalid. `[1,0,2,3]` is another valid topological order; `[2,0,1,3]` violates edges into vertex 2. DAG parent edge 1 may replace tied edge 0; selecting edge 3 as vertex 2's parent contradicts distance `-1`.

`tests/scale_benchmark.py` generates and checks full limits: `n=100000`, `q=250000` for DSU, and `n=100000`, `m=250000` for both forests, SCC, topo and DAG. Its chain reaches depth 100,000, with repeated parallel edges filling the edge limit. The actual summary is in `tests/scale_benchmark_actual.json`.

## Kruskal versus Prim benchmark

Command: `python tests/scale_benchmark.py`. The graph generator in that file uses a chain to ensure connectivity, then seeded `random.Random` endpoints and weights in `[-1000000,1000000]` to reach `m` edges. Each size uses the same edge list for both methods. Before timing, both forests are checked for equal cost, `n-1` distinct feasible edges and complete connectivity. Each method is warmed up once per graph. `time.perf_counter_ns()` measures one direct function call, including that method's graph/DSU construction and result creation, excluding graph generation, JSON parsing, serialization, process startup and compilation. Runs alternate method order. Times below are milliseconds; each row has three measurements per method.

Environment: Windows 11 build 26200, Python 3.14.7, Intel64 Family 6 Model 154 Stepping 3. Exact machine load and power state were not controlled.

| `n` | `m` | Seed | Kruskal runs | Median | Prim runs | Median |
| ---: | ---: | ---: | --- | ---: | --- | ---: |
| 1,000 | 4,000 | 314159 | 2.527, 2.370, 2.712 | 2.527 | 3.704, 4.740, 2.945 | 3.704 |
| 5,000 | 20,000 | 314160 | 16.658, 17.310, 15.999 | 16.658 | 19.860, 23.593, 25.247 | 23.593 |
| 20,000 | 80,000 | 314161 | 236.377, 246.885, 249.645 | 246.885 | 434.688, 421.806, 440.689 | 434.688 |

Kruskal was faster on these generated graphs. Its main work is sorting edge IDs; Prim builds two adjacency entries per undirected edge and maintains a lazy heap with stale entries. This observation is specific to these sizes, graph generator, Python runtime and machine. Both algorithms have the stated `O(n + m log(m+1))` upper bound; the timings do not prove one is always faster.

## Sources and tools

Source of the contract and examples: the supplied `Assignment_3_EN.pdf` and the template repository README and public validator. No external algorithm implementation was copied. AI tools were used as a supplementary aid to explain the algorithm classes, help locate errors during debugging, and review test results. I wrote the submitted code myself; AI did not generate the implementation. The reported outputs and measurements were produced by the commands above and checked against the test files.
