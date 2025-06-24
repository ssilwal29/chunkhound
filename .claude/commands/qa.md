Perform structured QA to the `semantic_search` and `regex_search` tools:
1. Pick a specific file in this project, search for it, and make sure you can correctly see the result
2. Add a new file, search for it, and make sure you can correctly see the result
3. Edit an existing file, search for it, and make sure you can correctly see the result
  - Cover adding contents, deleting contents and editing contents
4. Delete a file, search for it, and make sure you can correctly see the result
5. Run all of the above tests concurrently for all supported languages and file types.
6. List all supported languages. Thoroughly check all languages you didn't check. Make sure they all work. Don't skip any language.
7. Run a bunch of edits then immediately run searches. Make sure searches don't block.
8. **STOP IF ANY OF THE TESTS FAIL; CLEARY DOCUMENT THE FAILURE!!**

**Tips**:
- Wait a few seconds between a change and the test
- Measure the time it takes for changes to be reflected in the search results
- Use the task tool
- THE MCP SERVER OF THESE TOOLS IS CONTROLLED EXTERNALLY. DON'T TRY TO STOP IT
- ONLY EXERCISE THE EXISTING TOOLS. DO NOT WRITE HELPER SCRIPTS

**Deliverable**:
- A clear report of the findings – what works and what not.
- What works, what doesn't.
- How long does it take for updates to be reflected in search results.
- Keep it short clear; optimize for LLM ingestion.
