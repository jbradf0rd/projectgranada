#!/bin/bash

MAX_ITERATIONS=${1:-10}
ITERATION=0
PROMPT=$(cat prompt.md)

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
    ITERATION=$((ITERATION + 1))
    echo "=== Starting iteration $ITERATION of $MAX_ITERATIONS ==="
    
    # Run Claude with the prompt, capture output
    OUTPUT=$(claude --print "$PROMPT" 2>&1)
    
    echo "$OUTPUT"
    
    # Check if complete
    if echo "$OUTPUT" | grep -q "COMPLETE"; then
        echo "=== All tasks complete! ==="
        exit 0
    fi
    
    echo "=== Finished iteration $ITERATION ==="
    sleep 2
done

echo "=== Reached max iterations ($MAX_ITERATIONS) ==="