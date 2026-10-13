#!/bin/bash

set -e
TRACE_DIR=${1:?usage: $0 <trace_dir>}
OUT=results/task1/final
WARMUP=25000000
SIM=25000000
mkdir -p "$OUT"

./build_champsim.sh no        lru baseline
./build_champsim.sh ip_stride lru ipstride
./build_champsim.sh spp       lru spp

for t in trace1 trace2 trace3; do
    bin/hashed_perceptron-no-no-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-baseline \
        -warmup_instructions $WARMUP -simulation_instructions $SIM \
        -traces "$TRACE_DIR/$t.champsimtrace.gz" > "$OUT/${t}_baseline.txt" &
    bin/hashed_perceptron-no-ip_stride-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-ipstride \
        -warmup_instructions $WARMUP -simulation_instructions $SIM \
        -traces "$TRACE_DIR/$t.champsimtrace.gz" > "$OUT/${t}_ipstride.txt" &
    bin/hashed_perceptron-no-spp-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-spp \
        -warmup_instructions $WARMUP -simulation_instructions $SIM \
        -traces "$TRACE_DIR/$t.champsimtrace.gz" > "$OUT/${t}_spp.txt" &
done
wait
