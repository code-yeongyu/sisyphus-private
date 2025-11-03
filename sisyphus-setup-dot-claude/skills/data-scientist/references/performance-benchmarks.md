# Performance Benchmarks

Based on 2024-2025 benchmarks comparing DuckDB and Polars performance characteristics.

## Operation Performance Comparison

| Operation Type      | Winner      | Speed Advantage | When to Use                                    |
|---------------------|-------------|-----------------|------------------------------------------------|
| **Filtering**       | **Polars**  | **128x faster** | Single-table filters, predicate pushdown       |
| **Sorting**         | **Polars**  | **12x faster**  | ORDER BY operations, ranking                   |
| **Joins**           | **DuckDB**  | **3x faster**   | Multi-table joins, especially complex joins    |
| **Aggregations**    | **DuckDB**  | **4x faster**   | GROUP BY, complex aggregations                 |
| **Window Funcs**    | **Polars**  | **3-5x faster** | RANK, LAG/LEAD, running totals                 |
| **Transformations** | **Polars**  | **2x faster**   | Pivot, melt, string operations                 |
| **Direct Query**    | **DuckDB**  | **∞ faster**    | Ad-hoc exploration without loading to memory   |
| **Streaming**       | **Polars**  | **Handles OOM** | Datasets larger than RAM                       |

## Operation Detection Keywords

Automatically detect operation types from user requests:

- **Filter**: "where", "filter", "condition", "select rows", "find"
- **Sort**: "sort", "order", "top", "bottom", "rank"
- **Join**: "join", "merge", "combine tables"
- **Aggregate**: "group", "sum", "avg", "count", "mean", "total", "aggregate"
- **Transform**: "pivot", "melt", "reshape", "string operations", "clean", "transform"
- **Window**: "running", "cumulative", "lag", "lead", "rank", "partition"

## Benchmarking Notes

- Benchmarks conducted with typical data science workloads (1M-100M rows)
- Performance advantages are approximate and vary by dataset characteristics
- Both tools are significantly faster than pandas (10-50x improvement)
- Real-world performance depends on data types, cardinality, and hardware
