# Runtime Performance Investigation - May 15 2026

This note documents the second Hermes 10x pass: not just startup, but what
happens while the agent is being used in messages, tasks, delegated subagents,
tool calls, and persistence.

## What I Read

Official Hermes docs:

- [Agent Loop Internals](https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop/)
- [Tools Runtime](https://hermes-agent.nousresearch.com/docs/developer-guide/tools-runtime)
- [Delegation & Parallel Work](https://hermes-agent.nousresearch.com/docs/guides/delegation-patterns/)
- [Context Compression and Caching](https://hermes-agent.nousresearch.com/docs/developer-guide/context-compression-and-caching/)

Research papers used as design inspiration:

- [FrugalGPT](https://arxiv.org/abs/2305.05176): route work through cheaper
  paths first, only escalating when needed.
- [LLMLingua](https://arxiv.org/abs/2310.05736): reduce prompt/runtime cost by
  compressing information before inference.
- [vLLM / PagedAttention](https://arxiv.org/abs/2309.06180): treat scarce
  runtime state as a cache/memory-management problem.
- [RouteLLM](https://arxiv.org/abs/2406.18665): routing decisions can preserve
  quality while reducing spend.

## Translation Into Hermes Logic

The practical rule is: before Hermes spends model tokens, thread time, HTTP
probes, SQLite writes, or UI events, ask whether that work can produce useful
signal.

That maps directly onto Hermes runtime paths:

- Agent loop: build fewer avoidable payloads and make context checks cheaper.
- Tools runtime: cache stable availability and dispatch metadata.
- Delegation: avoid serial subagent overhead before parallel work begins.
- Session persistence: batch writes so many small messages share one
  transaction.
- TUI/config: reload only when the relevant config fingerprint changed.

## New Runtime Change

Added a fast negative preflight for numeric loopback endpoints in
`agent/model_metadata.py`.

Before this change, a dead custom local endpoint such as
`http://127.0.0.1:9/v1` made agent/subagent construction perform repeated HTTP
metadata probes. Each probe could wait on a connect timeout. The same issue
hurts delegated tasks because each child agent rebuilds its own context
compressor and context-length metadata.

Now Hermes does a narrow TCP reachability check for numeric loopback endpoints.
If the port is closed, it caches that negative result briefly and returns the
fallback context length immediately. This keeps normal remote/private-LAN
metadata behavior intact while making the common "local endpoint down" case
cheap.

![Dead endpoint fast path](assets/10x-fast/runtime-local-endpoint-fast-path.svg)

## Runtime Benchmark

Command:

```bash
python scripts/benchmark_runtime_usage.py -n 3
```

Current local Windows results after the fast path:

| Case | Median | Signal |
| --- | ---: | --- |
| `agent_init_file_terminal` | 4.9729s | 10.34x faster than the preflight baseline of 51.4181s |
| `agent_init_default_tools` | 5.0176s | 9.10x faster than the preflight baseline of 45.6670s |
| `delegate_child_build` | 4.9308s | 9.31x faster than the preflight baseline of 45.9254s |
| `parallel_tool_batch_sleep` | 0.0551s | 5.41x faster than sequential equivalent |
| `tool_dispatch_noop` | 0.0983s | 0.0341ms per dispatch |
| `parallel_guard_read_files` | 6.9878s | 0.7465ms per parallel safety decision |
| `session_append_messages_batch` | 0.0187s | 18.37x faster than per-message loop writes |

![Runtime benchmark suite](assets/10x-fast/runtime-benchmark-suite.svg)

## Visual Summary

Generated conceptual assets:

![Generated runtime before/after](assets/10x-fast/generated/runtime-before-after.png)

![Generated runtime before/after alternate](assets/10x-fast/generated/runtime-before-after-alt.png)

![Generated research to code](assets/10x-fast/generated/research-to-code.png)

![Generated parallel runtime](assets/10x-fast/generated/parallel-runtime.png)

Deterministic Markdown/SVG diagrams:

![Research principles map](assets/10x-fast/research-principles-map.svg)

## What This Means

We can honestly say the current branch has:

- Startup/tool-schema improvements in the 2x-4x range.
- SQLite session append throughput around 18x-25x faster depending on sample.
- Parallel tool execution around 5x faster for independent I/O-bound batches.
- A real 9x-10x runtime win for the dead local endpoint/subagent construction
  path, which was a practical "Hermes feels stuck before using the model"
  problem.

This is not a blanket "Hermes is 10x faster in every path" claim. It is a
measured 10x class win for a concrete runtime bottleneck, plus broader 2x-25x
wins on other hot paths.

## Next Safe Runtime Targets

- Instrument `delegate_task` with phase timings: config, credential resolution,
  child build, queue wait, run, aggregation.
- Reduce repeated delegation config loads per child.
- Investigate a reusable tool-call executor, but only after preserving
  thread-local approval, interrupt, sudo, and activity semantics.
- Measure `_save_session_log()` rewrite cost on long sessions before changing
  persistence format.
- Add opt-in runtime telemetry for message count, chars, tool result size,
  API payload build time, and JSON-RPC event burst rate.
