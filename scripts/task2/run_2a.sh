#!/bin/bash
set -e
cd "$(dirname "$0")/../.."

TRACE_DIR=${TRACE_DIR:-$HOME/pa2_traces}
WARMUP=${WARMUP:-25000000}
SIM=${SIM:-25000000}
OUT=${OUT:-results/task2/task2a}

BUILD=$(mktemp -d)
trap 'rm -rf "$BUILD"' EXIT
cp -r Makefile branch inc prefetcher replacement src "$BUILD"/
tr -d '\r' < build_champsim.sh > "$BUILD/build_champsim.sh"
mkdir -p bin $OUT

for policy in lru rrip irrip; do
    echo "building $policy"
    (cd "$BUILD" && TERM=dumb bash build_champsim.sh no $policy $policy > build_$policy.log 2>&1) || { tail -20 "$BUILD/build_$policy.log"; exit 1; }
    bin=$(basename "$BUILD"/bin/*-1core-$policy)
    cp "$BUILD/bin/$bin" bin/
    for t in trace1 trace2 trace3; do
        bin/$bin -warmup_instructions $WARMUP -simulation_instructions $SIM -traces $TRACE_DIR/$t.champsimtrace.gz > $OUT/${t}_$policy.txt 2>&1 &
    done
done
wait

for f in $OUT/trace*_{lru,rrip,irrip}.txt; do
    grep -q "Region of Interest" $f || { echo "incomplete run: $f"; exit 1; }
    [ "$(grep '^L1D PREFETCH  REQUESTED' $f | awk '{print $4}')" = 0 ] || { echo "unexpected L1D prefetches: $f"; exit 1; }
done
echo "task2a done"
