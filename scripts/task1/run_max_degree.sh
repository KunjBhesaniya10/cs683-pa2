#!/bin/bash
# dynamic degree range 1..MAX_DEGREE for MAX_DEGREE = 2..6.
# defined in prefetcher/spp.l1d_pref.

# Output: results/task1/max_degree/<trace>_max<D>.txt

set -e
TRACE_DIR=${1:?usage: $0 <trace_dir>}
OUT=results/task1/max_degree
WARMUP=25000000
SIM=25000000
mkdir -p "$OUT"

for max in 2 3 4 5 6; do
    name=max$max
    start=$(( max < 3 ? max : 3 ))

    rm -f obj/prefetcher/l1d_prefetcher.o
    EXTRA_FLAGS="-DACC_LOW=0.40 -DACC_HIGH=0.50 -DMAX_DEGREE=$max -DPREFETCH_DEGREE=$start" \
        ./build_champsim.sh spp lru $name

    for t in trace1 trace2 trace3; do
        bin/hashed_perceptron-no-spp-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-$name \
            -warmup_instructions $WARMUP -simulation_instructions $SIM \
            -traces "$TRACE_DIR/$t.champsimtrace.gz" > "$OUT/${t}_$name.txt" &
    done
done
wait
