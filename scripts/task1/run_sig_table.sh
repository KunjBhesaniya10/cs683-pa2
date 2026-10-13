#!/bin/bash
# signature table size, SIG_BITS = 7..10 (128..1024 entries).
# Output: results/task1/sig_table/<trace>_sig<BITS>.txt

set -e
TRACE_DIR=${1:?usage: $0 <trace_dir>}
OUT=results/task1/sig_table
WARMUP=25000000
SIM=25000000
mkdir -p "$OUT"

for bits in 7 8 9 10; do
    name=sig$bits

    rm -f obj/prefetcher/l1d_prefetcher.o
    EXTRA_FLAGS="-DSIG_BITS=$bits" ./build_champsim.sh spp lru $name

    for t in trace1 trace2 trace3; do
        bin/hashed_perceptron-no-spp-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-$name \
            -warmup_instructions $WARMUP -simulation_instructions $SIM \
            -traces "$TRACE_DIR/$t.champsimtrace.gz" > "$OUT/${t}_$name.txt" &
    done
done
wait
