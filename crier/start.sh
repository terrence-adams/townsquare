#!/bin/sh
# Town Crier launcher. Idempotent.
#
# Guards on the LISTENING PORT rather than a process-name match. A process-name
# guard was tried first and failed under busybox pgrep, starting a second
# instance that died on "address already in use". The port is what actually
# indicates "already serving".
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="${TS_LOG:-$DIR/crier.log}"
[ -f "$DIR/config.env" ] && . "$DIR/config.env"
PORT="${TS_BIND_PORT:-8787}"

if curl -s -m 5 -o /dev/null "http://127.0.0.1:$PORT/health" 2>/dev/null; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start.sh: already serving on $PORT" >> "$LOG"
    exit 0
fi
cd "$DIR" || exit 1
nohup "${TS_PYTHON:-$DIR/.venv/bin/python}" "$DIR/crier.py" >> "$LOG" 2>&1 &
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) start.sh: started pid $!" >> "$LOG"
