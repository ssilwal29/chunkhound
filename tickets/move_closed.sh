#!/bin/bash
#
# Utility script to move closed tickets to tickets/closed/ directory.
#
# Scans all .md files in tickets/ directory and moves ones with closed status
# to tickets/closed/ subdirectory.
#
# Closed status indicators:
# - Status: FIXED
# - Status: Fixed  
# - Status: Done
# - Status: WONTFIX

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TICKETS_DIR="$SCRIPT_DIR"
CLOSED_DIR="$TICKETS_DIR/closed"

# Create closed directory if it doesn't exist
mkdir -p "$CLOSED_DIR"

moved_count=0

# Function to check if ticket is closed
is_ticket_closed() {
    local file="$1"
    
    # Skip CLAUDE.md
    if [[ "$(basename "$file")" == "CLAUDE.md" ]]; then
        return 1
    fi
    
    # Look for Status line and check if it's closed
    if grep -q "^\*\*Status\*\*:\s*\(FIXED\|Fixed\|Done\|WONTFIX\)" "$file"; then
        return 0
    fi
    
    return 1
}

# Process all .md files in tickets directory
for file in "$TICKETS_DIR"/*.md; do
    # Skip if no .md files exist
    [[ ! -f "$file" ]] && continue
    
    if is_ticket_closed "$file"; then
        filename="$(basename "$file")"
        echo "Moving $filename -> closed/"
        mv "$file" "$CLOSED_DIR/"
        ((moved_count++))
    fi
done

echo
echo "Moved $moved_count closed tickets to tickets/closed/"