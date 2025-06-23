# [BUG] OpenAI Embedding Token Limit Exceeded

**Date**: 2025-06-23  
**Priority**: High  
**Status**: Completed  
**Files**: `providers/embeddings/openai_provider.py`

## Problem

OpenAI API rejects embedding requests due to token limit:
```
ERROR | Failed to generate embeddings: Error code: 400 - {'error': {'message': "This model's maximum context length is 8192 tokens, however you requested 29854 tokens (29854 in your prompt; 0 for the completion). Please reduce your prompt; or completion length.", 'type': 'invalid_request_error', 'param': None, 'code': None}}
```

## Root Cause

From codebase analysis:
1. `text-embedding-3-small` model has 8,192 token limit
2. Current batching sends 29,854+ tokens in single request
3. No token counting or batch size adjustment based on token limits
4. Large code chunks cause batch to exceed limits

## Solution

Implement token-aware batching:
- Add token counting before API requests
- Implement dynamic batch sizing based on token limits
- Split large individual chunks that exceed limits
- Add retry logic with smaller batches

## Technical Details

- Model: `text-embedding-3-small` (8,192 token limit)
- Current batch_size: 100 items
- Need: Token-based batching instead of item-based

## Acceptance Criteria

- [x] No token limit exceeded errors
- [x] Dynamic batch sizing based on token count
- [x] Handle individual chunks that exceed token limits
- [x] Maintain embedding generation throughput
- [x] Add token limit configuration per model

## Solution Implemented

Fixed token limit issue in `providers/embeddings/openai_provider.py`:

1. **Token-aware batching**: Added `estimate_batch_tokens()` and `get_model_token_limit()` methods
2. **Dynamic batch sizing**: Modified `embed_batch()` to respect 8,192 token limit with safety margin
3. **Oversized chunk handling**: Automatically splits individual texts exceeding token limits
4. **Model configuration**: Added `max_tokens` to model config for `text-embedding-3-small/large` and `ada-002`

Tests pass, preventing token limit exceeded errors while maintaining throughput.