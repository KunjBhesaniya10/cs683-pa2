#!/bin/bash

# accuracy-throttling thresholds (ACC_LOW, ACC_HIGH).
# varying ACC_LOW and ACC_HIGH such that ACC_HIGH - ACC_LOW >= 0.10
# Output: results/task1/acc_grid/<trace>_low<LOW>_high<HIGH>.txt

set -e
TRACE_DIR=${1:?usage: $0 <trace_dir>}
OUT=results/task1/acc_grid
WARMUP=25000000
SIM=25000000
mkdir -p "$OUT"

for low in 10 20 30 40 50; do
    for high in 40 50 60 70 80; do
        if [ $((high - low)) -lt 10 ]; then continue; fi
        name=low$(printf %03d $low)_high$(printf %03d $high)

        rm -f obj/prefetcher/l1d_prefetcher.o
        EXTRA_FLAGS="-DMAX_DEGREE=4 -DACC_LOW=0.$(printf %02d $low) -DACC_HIGH=0.$(printf %02d $high)" \
            ./build_champsim.sh spp lru $name

        for t in trace1 trace2 trace3; do
            bin/hashed_perceptron-no-spp-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-$name \
                -warmup_instructions $WARMUP -simulation_instructions $SIM \
                -traces "$TRACE_DIR/$t.champsimtrace.gz" > "$OUT/${t}_$name.txt" &
        done
    done
done
wait
