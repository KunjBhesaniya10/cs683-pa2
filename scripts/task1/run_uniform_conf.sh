#!/bin/bash
# uniform-mode confidence threshold, UNIFORM_CONF_THRESHOLD = 1..3 (2-bit counter).
# Output: results/task1/uniform_conf/<trace>_uc<N>.txt

set -e
TRACE_DIR=${1:?usage: $0 <trace_dir>}
OUT=results/task1/uniform_conf
WARMUP=25000000
SIM=25000000
mkdir -p "$OUT"

for n in 1 2 3; do
    name=uc$n

    rm -f obj/prefetcher/l1d_prefetcher.o
    EXTRA_FLAGS="-DUNIFORM_CONF_THRESHOLD=$n" ./build_champsim.sh spp lru $name

    for t in trace1 trace2 trace3; do
        bin/hashed_perceptron-no-spp-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-$name \
            -warmup_instructions $WARMUP -simulation_instructions $SIM \
            -traces "$TRACE_DIR/$t.champsimtrace.gz" > "$OUT/${t}_$name.txt" &
    done
done
wait
