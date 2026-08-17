#!/usr/bin/env sh
# The out-of-graph entry point. graph_gen globs *.py only, so this caller is invisible and
# `wired_pipeline.run_pipeline` looks dead to S1. Verbatim honest limit:
# "entry points outside the graph look dead".
python -c "from wired_pipeline import run_pipeline; print(run_pipeline({'go': True}))"
