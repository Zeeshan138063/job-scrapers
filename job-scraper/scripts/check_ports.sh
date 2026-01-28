#!/bin/bash

BLUE='\033[0;34m'
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

PORTS=(6379 8080 3000 9090)

echo -e "${BLUE}Checking for port conflicts...${NC}"

for port in "${PORTS[@]}"; do
    # Check if port is in use
    if ss -lptn "sport = :$port" | grep -q "$port"; then
        echo -e "${RED}[BUSY]${NC} Port $port is in use."
        
        # Try to find PID/Name
        # Note: This might require sudo to see all processes
        pid=$(lsof -t -i:$port 2>/dev/null)
        if [ -n "$pid" ]; then
            name=$(ps -p $pid -o comm=)
            echo -e "       Process: $name (PID: $pid)"
            echo -e "       To kill: sudo kill -9 $pid"
        else
            echo -e "       Process details hidden (requires root)."
            echo -e "       Try: sudo lsof -i :$port"
        fi
    else
        echo -e "${GREEN}[FREE]${NC} Port $port is available."
    fi
done
