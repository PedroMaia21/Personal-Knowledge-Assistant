# Distance Investigation Findings

## Summary

| Metric | Value |
|--------|-------|
| Best (lowest) distance | `0.2627` |
| Worst (highest) distance | `0.6182` |
| Average distance | `0.4841` |
| Median distance | `0.4744` |

## Interpretation

> Fill these in after reviewing the per-query table below.

- **Excellent retrieval (0.90+ similarity):** distance ≈ `___`
- **Good retrieval (0.80–0.90):** distance ≈ `___`
- **Acceptable (0.70–0.80):** distance ≈ `___`
- **Suspicious (<0.70):** distance > `___`

## Per-Query Results

| Query | Best distance | Worst distance | Avg distance |
|-------|--------------|----------------|-------------|
| machine learning | 0.3891 | 0.444 | 0.4154 |
| productivity systems | 0.4148 | 0.4823 | 0.4495 |
| weekly review | 0.3589 | 0.5558 | 0.4783 |
| action items | 0.4419 | 0.5191 | 0.4879 |
| project planning | 0.4067 | 0.4385 | 0.4269 |
| goals and priorities | 0.3957 | 0.4161 | 0.4052 |
| time management | 0.3956 | 0.4667 | 0.4316 |
| decision making | 0.3628 | 0.504 | 0.4434 |
| knowledge management | 0.4821 | 0.5349 | 0.5033 |
| note taking strategies | 0.4079 | 0.4603 | 0.4269 |
| software development | 0.4829 | 0.4834 | 0.4831 |
| personal growth | 0.4632 | 0.5512 | 0.5207 |
| learning strategies | 0.44 | 0.5107 | 0.4744 |
| task prioritization | 0.3673 | 0.4164 | 0.3997 |
| focus and deep work | 0.2627 | 0.4746 | 0.39 |
| automation | 0.5203 | 0.5366 | 0.5287 |
| AI tools | 0.4303 | 0.4635 | 0.4497 |
| retrospective review | 0.445 | 0.484 | 0.4686 |
| blocker identification | 0.5073 | 0.565 | 0.545 |
| habit building | 0.39 | 0.4905 | 0.4449 |
| quantum physics equations | 0.5797 | 0.6072 | 0.5938 |
| French cuisine recipes | 0.6031 | 0.6182 | 0.6084 |
| stock market prediction | 0.5368 | 0.5833 | 0.5568 |
| climate change policy | 0.5577 | 0.6043 | 0.5805 |
| ancient Roman history | 0.5797 | 0.5982 | 0.5894 |

## Raw JSON

```json
[
  {
    "query": "machine learning",
    "best_distance": 0.3891,
    "worst_distance": 0.444,
    "avg_distance": 0.4154
  },
  {
    "query": "productivity systems",
    "best_distance": 0.4148,
    "worst_distance": 0.4823,
    "avg_distance": 0.4495
  },
  {
    "query": "weekly review",
    "best_distance": 0.3589,
    "worst_distance": 0.5558,
    "avg_distance": 0.4783
  },
  {
    "query": "action items",
    "best_distance": 0.4419,
    "worst_distance": 0.5191,
    "avg_distance": 0.4879
  },
  {
    "query": "project planning",
    "best_distance": 0.4067,
    "worst_distance": 0.4385,
    "avg_distance": 0.4269
  },
  {
    "query": "goals and priorities",
    "best_distance": 0.3957,
    "worst_distance": 0.4161,
    "avg_distance": 0.4052
  },
  {
    "query": "time management",
    "best_distance": 0.3956,
    "worst_distance": 0.4667,
    "avg_distance": 0.4316
  },
  {
    "query": "decision making",
    "best_distance": 0.3628,
    "worst_distance": 0.504,
    "avg_distance": 0.4434
  },
  {
    "query": "knowledge management",
    "best_distance": 0.4821,
    "worst_distance": 0.5349,
    "avg_distance": 0.5033
  },
  {
    "query": "note taking strategies",
    "best_distance": 0.4079,
    "worst_distance": 0.4603,
    "avg_distance": 0.4269
  },
  {
    "query": "software development",
    "best_distance": 0.4829,
    "worst_distance": 0.4834,
    "avg_distance": 0.4831
  },
  {
    "query": "personal growth",
    "best_distance": 0.4632,
    "worst_distance": 0.5512,
    "avg_distance": 0.5207
  },
  {
    "query": "learning strategies",
    "best_distance": 0.44,
    "worst_distance": 0.5107,
    "avg_distance": 0.4744
  },
  {
    "query": "task prioritization",
    "best_distance": 0.3673,
    "worst_distance": 0.4164,
    "avg_distance": 0.3997
  },
  {
    "query": "focus and deep work",
    "best_distance": 0.2627,
    "worst_distance": 0.4746,
    "avg_distance": 0.39
  },
  {
    "query": "automation",
    "best_distance": 0.5203,
    "worst_distance": 0.5366,
    "avg_distance": 0.5287
  },
  {
    "query": "AI tools",
    "best_distance": 0.4303,
    "worst_distance": 0.4635,
    "avg_distance": 0.4497
  },
  {
    "query": "retrospective review",
    "best_distance": 0.445,
    "worst_distance": 0.484,
    "avg_distance": 0.4686
  },
  {
    "query": "blocker identification",
    "best_distance": 0.5073,
    "worst_distance": 0.565,
    "avg_distance": 0.545
  },
  {
    "query": "habit building",
    "best_distance": 0.39,
    "worst_distance": 0.4905,
    "avg_distance": 0.4449
  },
  {
    "query": "quantum physics equations",
    "best_distance": 0.5797,
    "worst_distance": 0.6072,
    "avg_distance": 0.5938
  },
  {
    "query": "French cuisine recipes",
    "best_distance": 0.6031,
    "worst_distance": 0.6182,
    "avg_distance": 0.6084
  },
  {
    "query": "stock market prediction",
    "best_distance": 0.5368,
    "worst_distance": 0.5833,
    "avg_distance": 0.5568
  },
  {
    "query": "climate change policy",
    "best_distance": 0.5577,
    "worst_distance": 0.6043,
    "avg_distance": 0.5805
  },
  {
    "query": "ancient Roman history",
    "best_distance": 0.5797,
    "worst_distance": 0.5982,
    "avg_distance": 0.5894
  }
]
```
