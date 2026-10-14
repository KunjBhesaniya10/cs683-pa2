#!/bin/bash
# IP table size: 24, 64, 128, 256 entries with an IP tag wide enough for each size.

set -e
TRACE_DIR=${1:?usage: $0 <trace_dir>}
OUT=results/task1/ip_table
WARMUP=25000000
SIM=25000000
mkdir -p "$OUT"

for cfg in "24 0xFF" "64 0x1FF" "128 0x3FF" "256 0x3FF"; do
    set -- $cfg
    name=ip$1

    rm -f obj/prefetcher/l1d_prefetcher.o
    EXTRA_FLAGS="-DIP_TRACKER_COUNT=$1 -DMASK_IP=$2" ./build_champsim.sh spp lru $name

    for t in trace1 trace2 trace3; do
        bin/hashed_perceptron-no-spp-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-$name \
            -warmup_instructions $WARMUP -simulation_instructions $SIM \
            -traces "$TRACE_DIR/$t.champsimtrace.gz" > "$OUT/${t}_$name.txt" &
    done
done
wait
