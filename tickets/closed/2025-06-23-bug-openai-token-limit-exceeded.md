# 2025-06-23 - [BUG] OpenAI Token Limit Exceeded
**Priority**: High

`BadRequestError` with "maximum context length exceeded" when batches contain too many tokens for OpenAI's 8,192 token limit.

# History

## 2025-06-23-1
Initial fix: Added token-aware batching and model configuration. Issue partially resolved but used inefficient half-splitting on errors.

## 2025-06-23-2
Improved error handling in `_embed_batch_internal()`:
- Added `BadRequestError` detection for token limit exceeded
- Implemented optimal token-based splitting: `(total_tokens + limit - 1) // limit`
- Distributes texts evenly across calculated number of batches
- Single-text chunking for oversized individual texts
- All tests pass, no more token limit errors