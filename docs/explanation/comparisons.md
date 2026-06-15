# Tools compared

No other tool does quite what blanket does, but a large body of academic and industrial work addresses testing
concurrent code, and some of it is close.

## Stateless model checking

The nearest field is stateless model checking (SMC). Tools include Microsoft's CHESS, AWS's Shuttle, Rust's Loom, GenMC,
and Nidhugg. The field has been active for two decades.

SMC automates the exploration of thread interleavings. The tool runs your test many times, each time making different
scheduling choices, aiming to cover as many distinct interleavings as it can. Modern SMC tools prune redundant orderings
with dynamic partial-order reduction, and bias the search toward likely bugs with probabilistic strategies such as the
Probabilistic Concurrency Testing algorithm.

The trade-off is that most SMC tools reimplement the synchronization primitives so they can inspect and control
execution finely. Your program then runs against the tool's reimplementation rather than the real primitive.

## Coyote

Microsoft's Coyote sits closer to blanket in spirit. It is an SMC tool for .NET that records the sequence of scheduling
decisions leading to any bug it finds, then replays that recording to reproduce the bug. The recording resembles a
blanket scheduler script produced automatically. The recordings appear to be machine-generated and machine-replayed,
rather than written or edited by hand the way a blanket script is.

## What sets blanket apart

The difference is intent. The other tools aim to discover concurrency bugs. blanket aims to recreate known concurrency
scenarios, declaratively, in code you write yourself.

Could you use blanket for SMC? Probably. blanket is not tuned for raw speed, so an SMC tool would likely want something
faster. The other direction fits better: a Python SMC tool could emit blanket scheduler code as output, much like a
Coyote recording. Once it found a bug, it could write a blanket script that reproduces it, and you could drop that
script into your regression suite.
