#!/bin/bash
set -e
cd "$(dirname "$0")/../.."

TRACE_DIR=${TRACE_DIR:-$HOME/pa2_traces}
WARMUP=${WARMUP:-25000000}
SIM=${SIM:-25000000}
OUT=${OUT:-results/task2/task2b/threshold}

BUILD=$(mktemp -d)
trap 'rm -rf "$BUILD"' EXIT
cp -r Makefile branch inc prefetcher replacement src "$BUILD"/
tr -d '\r' < build_champsim.sh > "$BUILD/build_champsim.sh"
mkdir -p bin $OUT

for e in 0.30:3:10 0.40:2:5 0.45:9:20 0.50:1:2 0.60:3:5 0.70:7:10; do
    IFS=: read th num den <<< "$e"
    name=dyn_t$th
    flags="-DTHRESHOLD_NUM=$num -DTHRESHOLD_DEN=$den"
    echo "building $name ($flags)"
    (cd "$BUILD" && EXTRA_FLAGS="$flags" TERM=dumb bash build_champsim.sh no dyn_irrip $name > build_$name.log 2>&1) || { tail -20 "$BUILD/build_$name.log"; exit 1; }
    bin=$(basename "$BUILD"/bin/*-1core-$name)
    cp "$BUILD/bin/$bin" bin/
    for t in trace1 trace2 trace3; do
        bin/$bin -warmup_instructions $WARMUP -simulation_instructions $SIM -traces $TRACE_DIR/$t.champsimtrace.gz > $OUT/${t}_$name.txt 2>&1 &
    done
done
wait

for f in $OUT/trace*_dyn_t*.txt; do
    grep -q "Region of Interest" $f || { echo "incomplete run: $f"; exit 1; }
    [ "$(grep '^L1D PREFETCH  REQUESTED' $f | awk '{print $4}')" = 0 ] || { echo "unexpected L1D prefetches: $f"; exit 1; }
done
echo "task2b threshold done"
