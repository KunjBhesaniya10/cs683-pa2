#!/bin/bash
# Task 3: SPP with prefetch-aware dynamic I-RRIP at L2.
set -e
cd "$(dirname "$0")/../.."

TRACE_DIR=${TRACE_DIR:-$HOME/pa2_traces}
WARMUP=${WARMUP:-25000000}
SIM=${SIM:-25000000}
OUT=${OUT:-results/task3}

BUILD=$(mktemp -d)
trap 'rm -rf "$BUILD"' EXIT
cp -r Makefile branch inc prefetcher replacement src "$BUILD"/
tr -d '\r' < build_champsim.sh > "$BUILD/build_champsim.sh"
mkdir -p bin $OUT

CONFIGS="baseline:no:lru:
spp:spp:lru:
dyn:no:dyn_irrip:
spp_dyn:spp:dyn_irrip:"

while IFS=: read name pref policy flags; do
    echo "building $name ($pref + $policy $flags)"
    (cd "$BUILD" && EXTRA_FLAGS="$flags" TERM=dumb bash build_champsim.sh $pref $policy t3_$name > build_$name.log 2>&1) || { tail -20 "$BUILD/build_$name.log"; exit 1; }
    bin=$(basename "$BUILD"/bin/*-1core-t3_$name)
    cp "$BUILD/bin/$bin" bin/
    for t in trace1 trace2 trace3; do
        bin/$bin -warmup_instructions $WARMUP -simulation_instructions $SIM -traces $TRACE_DIR/$t.champsimtrace.gz > $OUT/${t}_$name.txt 2>&1 &
    done
done <<< "$CONFIGS"
wait

for f in $OUT/trace*_*.txt; do
    grep -q "Region of Interest" $f || { echo "incomplete run: $f"; exit 1; }
done
echo "task3 done"
