import { describe, expect, it } from 'vitest'
import { TIMING_LABELS } from '../api/openapi.generated'
import { STRINGS } from './translate'

const fam = (prefix: string, ids: readonly string[]) => ids.map((i) => `${prefix}${i}`)
const FAMILIES = [
  ...fam('ui.flow.stage.', ['consent', 'photo', 'check', 'results', 'schedule']),
  ...fam('ui.flow.problem.', ['expired', 'consent_required', 'blocked', 'not_found', 'not_ready', 'queue_full', 'too_many_documents', 'too_large', 'pdf', 'unsupported', 'invalid', 'network', 'server', 'unknown']),
  ...fam('ui.flow.timing.', TIMING_LABELS),
  ...fam('ui.flow.level.', ['major', 'moderate', 'minor', 'unknown']),
  ...fam('ui.flow.review.needs.', ['action', 'ack', 'formulary', 'strength', 'schedule']),
  ...fam('ui.flow.review.level.', ['must_confirm', 'note', 'none']),
  ...fam('ui.flow.docs.state.', ['queued', 'extracting', 'normalising', 'awaiting_confirmation', 'failed', 'expired', 'deleted']),
  ...fam('ui.flow.start.step', ['1.title', '1.body', '2.title', '2.body', '3.title', '3.body']),
  ...fam('ui.flow.processing.stage.', ['queued', 'extracting', 'normalising']),
]
describe('dynamic string families (keys built at run time)', () => {
  it('exist in en, ta and hi', () => {
    for (const lang of ['en', 'ta', 'hi'] as const) expect(FAMILIES.filter((k) => !STRINGS[lang][k]), lang).toEqual([])
  })
})
