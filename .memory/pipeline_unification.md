# Pipeline Unification Changes

## Date: 2025-01-XX

## Major Change: Unified Pipeline Architecture

### Before (Two-Phase Separate):
- Phase 1 (Analysis): Every 6 hours
- Phase 2 (Creation): Every 12 hours
- Jobs could run independently
- Manual trigger had 3 options: analysis, creation, both

### After (Unified Sequential):
- Full Pipeline: Every 6 hours
- Jobs always run sequentially: discover → analyze → process → publish
- Manual trigger has simple boolean: "Run full pipeline" (default: true)
- Phase 2 always has fresh data from Phase 1

## Key Files Modified

1. **`.github/workflows/main.yml`**
   - Single schedule: `0 */6 * * *`
   - Added job dependencies with `needs`
   - Simplified `workflow_dispatch` interface
   - Fixed artifact download bugs (removed `continue-on-error: true`)

2. **`src/pipeline_orchestrator.py`**
   - Added `run_full_pipeline()` method
   - Coordinates both phases sequentially
   - Returns combined results

3. **`docs/TWO_PHASE_PIPELINE.md`**
   - Renamed to "Unified Video Processing Pipeline"
   - Updated all references to reflect sequential execution

## Benefits

1. **Consistency**: Analysis and creation always run together
2. **Data Freshness**: Phase 2 uses fresh Phase 1 results
3. **Simplicity**: Single schedule instead of two
4. **Reliability**: Sequential execution prevents race conditions
5. **Usability**: Clear "Run full pipeline" manual trigger

## Backward Compatibility

- ✅ No changes to configuration files
- ✅ Database schema unchanged
- ✅ `processor.py --phase` still works
- ✅ `publisher.py` unchanged
- ✅ Individual phase execution still possible

## Important Notes

- Pipeline runs every 6 hours automatically
- Manual trigger always runs complete pipeline by default
- All jobs must complete successfully for pipeline to finish
- Artifacts are properly passed between jobs
- Errors in early jobs prevent later jobs from running

## For Future Tasks

- Pipeline is now unified, so references to "two phase" should be updated to "unified pipeline"
- When adding new features, consider sequential execution
- Monitor job execution times to ensure they fit within GitHub limits
- Consider adding dashboard for real-time pipeline monitoring
