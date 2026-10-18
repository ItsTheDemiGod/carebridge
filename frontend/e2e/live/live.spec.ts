import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'
import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { openCard } from '../flowhelpers'

const ROOT = fileURLToPath(new URL('../../../', import.meta.url))
const SHOTS = `${ROOT}docs/screenshots/phase6c`
const REPORT = `${ROOT}docs/smoke/phase6c_live.json`
mkdirSync(SHOTS, { recursive: true })

type GT = { brand_name: string | null; generic_name: string | null; strength: string | null }
const groundTruth = (id: string): GT[] => JSON.parse(readFileSync(`${ROOT}data/ground_truth/${id}.json`, 'utf8')).medications

const FLOWS = [
  { n: 1, lang: 'en', cond: 'clean' },
  { n: 2, lang: 'ta', cond: 'clean', extra: 'hi' },
  { n: 3, lang: 'hi', cond: 'poor' },
] as const
const DOC = 'ds_037'
const sec = (a: number, b = Date.now()) => Math.round((b - a) / 100) / 10

async function shot(page: Page, flow: number, lang: string, name: string) {
  if (!/^(5review|6result)$/.test(name)) return // the screenshot budget keeps only the review and result pages (6 images)
  await page.waitForTimeout(500)
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.screenshot({ path: `${SHOTS}/f${flow}_${lang}_${name}.jpg`, type: 'jpeg', quality: 55, fullPage: true })
}

for (const F of FLOWS)
  test(`live flow ${F.n}: ${F.lang} session, ${F.cond} image`, async ({ browser }) => {
    const c = await browser.newContext({ reducedMotion: 'no-preference' })
    await c.addInitScript((l) => localStorage.setItem('carebridge.language', l), F.lang)
    const page = await c.newPage()
    const errors: string[] = []
    page.on('console', (m) => m.type() === 'error' && !/Failed to load resource: the server responded with a status of 4\d\d/.test(m.text()) && errors.push(m.text()))
    page.on('pageerror', (e) => errors.push(`pageerror ${e.message}`))
    const rep: Record<string, unknown> = { flow: F.n, lang: F.lang, image: `${F.cond}/${DOC}.png` }
    const T0 = Date.now()
    const api = (p: string) => page.request.get(`/api/v1${p}`)
    const json = async (p: string) => (await api(p)).json()
    const gt = groundTruth(DOC)

    // consent
    await page.goto('/start')
    await page.locator('h1').waitFor()
    await shot(page, F.n, F.lang, '1start')
    await page.locator('main .page-actions button').first().click()
    await page.waitForURL('**/consent')
    await page.locator('.purposes').waitFor()
    await shot(page, F.n, F.lang, '2consent')
    await page.locator('form.consent-article button[type=submit]').click()
    await page.waitForURL('**/upload')
    rep.t_consent_s = sec(T0)

    // upload + processing
    await page.locator('#file-pick').setInputFiles(`${ROOT}data/rendered/${F.cond}/${DOC}.png`)
    await page.locator('.preview img').waitFor()
    await shot(page, F.n, F.lang, '3upload')
    const tUp = Date.now()
    await page.locator('.preview .btn-primary').click()
    await page.waitForURL('**/processing')
    await page.getByRole('progressbar').waitFor()
    await shot(page, F.n, F.lang, '4processing')
    await page.waitForURL('**/review', { timeout: 6 * 60_000 })
    rep.t_extraction_to_review_s = sec(tUp)
    const id = page.url().split('/d/')[1].split('/')[0]
    const doc0 = await json(`/documents/${id}`)
    rep.at_review_arrival = { narrative: doc0.narrative, timings: doc0.timings }
    await page.locator('article.med-card').first().waitFor()

    // review: pick formulary drugs from ground-truth names (TEST ONLY), acknowledge every flag, confirm
    const tRev = Date.now()
    const before = await json(`/documents/${id}/result?lang=${F.lang}`)
    rep.before_confirmation = { counts: before.explanation.safety?.counts?.pairs_by_status, found: before.explanation.safety?.pair_results.filter((p: { status: string }) => p.status === 'interaction_found').length, confirm_first: before.confirm_first }
    const n = await page.locator('article.med-card').count()
    const decisions: string[] = []
    for (let i = 0; i < n; i++) {
      const cd = await openCard(page, i) // cards are listed needs-attention first; checked ones fold, so go by document index
      const quote = ((await cd.locator('blockquote').innerText()) ?? '').toLowerCase()
      const level = await cd.locator('.rv-chip').innerText()
      const match = gt.find((g) => [g.brand_name, g.generic_name].filter(Boolean).some((s) => quote.includes(String(s).toLowerCase()))) ?? gt[i]
      const radios = cd.locator('input[type=radio]')
      const hasNameReason = (await cd.locator('.reasons li[data-kind=name]').count()) > 0
      if (hasNameReason && match?.generic_name) {
        await radios.nth(1).check()
        const box = cd.getByRole('combobox').first()
        await box.fill(match.generic_name.slice(0, 5))
        const opt = cd.getByRole('option').filter({ hasText: new RegExp(match.generic_name, 'i') }).first()
        await opt.waitFor({ timeout: 10_000 })
        await opt.click()
        const st = cd.locator('.strengths input[type=radio]')
        const labels = await cd.locator('.strengths label').allInnerTexts()
        let k = labels.findIndex((l) => l.trim() === match.strength)
        if (k < 0) k = labels.length - 1 // "as on my label"
        await st.nth(k).check()
        decisions.push(`${i}:picker:${match.generic_name}`)
      } else {
        await radios.nth(0).check()
        decisions.push(`${i}:confirm(${level.trim()})`)
      }
      const acks = cd.locator('fieldset.acks input[type=checkbox]')
      for (let a = 0; a < (await acks.count()); a++) await acks.nth(a).check()
      const btn = cd.locator('.card-confirm .btn')
      if (await btn.isEnabled()) await btn.click()
      else decisions[decisions.length - 1] += ':LEFT_UNDECIDED'
    }
    rep.review_decisions = decisions
    await shot(page, F.n, F.lang, '5review')
    await page.locator('.summary-bar .btn').click()
    await page.locator('.saved-panel').waitFor()
    rep.t_review_s = sec(tRev)
    const doc1 = await json(`/documents/${id}`)
    rep.at_save = { narrative: doc1.narrative }
    const after = await json(`/documents/${id}/result?lang=${F.lang}`)
    rep.after_confirmation = { counts: after.explanation.safety?.counts?.pairs_by_status, found: after.explanation.safety?.pair_results.filter((p: { status: string }) => p.status === 'interaction_found').length, confirm_first: after.confirm_first }

    // results
    const tRes = Date.now()
    await page.locator('.page-actions a').first().click()
    await page.waitForURL('**/result')
    await page.locator('#result-panel').waitFor()
    await expect(page.locator('.preparing')).toHaveCount(0, { timeout: 8 * 60_000 })
    rep.t_result_narrative_wait_s = sec(tRes)
    const res = await json(`/documents/${id}/result?lang=${F.lang}`)
    const free = res.explanation.sections.filter((s: { id: string }) => ['follow_ups', 'advice', 'warnings'].includes(s.id)).flatMap((s: { lines: { provenance: string; text: Record<string, { provenance: string }> }[] }) => s.lines)
    const inLang = free.filter((l: { text: Record<string, { provenance: string }> }) => l.text[F.lang]?.provenance !== 'original_only').length
    rep.free_text_lines = { total: free.length, shown_in_language: inLang, original_english_fallback: free.length - inLang }
    rep.narrative_status = res.narrative_status
    rep.timings = (await json(`/documents/${id}`)).timings
    await shot(page, F.n, F.lang, '6result')
    const ax = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze()
    rep.axe_result_page = ax.violations.map((v) => `${v.impact} ${v.id} x${v.nodes.length}`)

    if ('extra' in F) {
      const tHi = Date.now()
      await page.getByRole('tab', { name: 'हिन्दी' }).click()
      let st = 'not_started'
      while (!['ready', 'failed'].includes(st) && Date.now() - tHi < 10 * 60_000) {
        await page.waitForTimeout(3000)
        st = (await json(`/documents/${id}/result?lang=hi`)).narrative_status.hi
      }
      const hi = await json(`/documents/${id}/result?lang=hi`)
      const hfree = hi.explanation.sections.filter((s: { id: string }) => ['follow_ups', 'advice', 'warnings'].includes(s.id)).flatMap((s: { lines: { text: Record<string, { provenance: string }> }[] }) => s.lines)
      rep.hindi_after_tamil = { status: st, seconds: sec(tHi), lines: hfree.length, in_hindi: hfree.filter((l: { text: Record<string, { provenance: string }> }) => l.text.hi?.provenance !== 'original_only').length }
      await expect(page.locator('.preparing')).toHaveCount(0, { timeout: 60_000 })
      await shot(page, F.n, 'hi', '6result_hindi_tab')
    }

    // schedule: one taken, one skipped
    await page.goto(`/d/${id}/schedule`)
    await page.locator('.slot').first().waitFor()
    const slots = page.locator('.slot')
    rep.slots = await slots.count()
    await slots.nth(0).locator('.slot-actions .btn').nth(0).click()
    if ((await slots.count()) > 1) await slots.nth(1).locator('.slot-actions .btn').nth(1).click()
    await expect(slots.nth(0).locator('.slot-actions .btn').nth(0)).toHaveAttribute('aria-pressed', 'true')
    await shot(page, F.n, F.lang, '7schedule')
    await page.goto(`/d/${id}/summary`)
    await page.locator('.summary-table').waitFor()
    rep.summary_rows = await page.locator('.summary-table tbody tr').count()
    await shot(page, F.n, F.lang, '8summary')

    // delete my data, then verify through the API that nothing remains
    await page.locator('.delete-btn').click()
    await page.getByRole('dialog').waitFor()
    await shot(page, F.n, F.lang, '9delete')
    await page.getByRole('dialog').locator('.btn-danger').click()
    await page.waitForURL(/\/$/)
    await page.locator('.deleted-note').waitFor()
    rep.receipt = await page.locator('.deleted-note').innerText()
    const s1 = await api('/session')
    const d1 = await api(`/documents/${id}`)
    const l1 = await api('/documents')
    rep.after_delete = { session: s1.status(), document: d1.status(), list: l1.status() }
    expect([s1.status(), d1.status(), l1.status()]).toEqual([401, 401, 401])
    const fresh = await page.request.post('/api/v1/sessions', { data: { language: 'en' }, headers: { 'X-CareBridge-Request': '1' } })
    rep.fresh_session_documents = (await fresh.json()).documents
    expect((await fresh.json()).documents).toBe(0)
    expect((await page.request.get(`/api/v1/documents/${id}`)).status()).toBe(403) // new session: no consent yet, and the old id is not reachable either
    await page.request.delete('/api/v1/session', { headers: { 'X-CareBridge-Request': '1' } })

    rep.console_errors = errors
    rep.total_s = sec(T0)
    appendFileSync(REPORT, JSON.stringify(rep) + '\n')
    expect(errors).toEqual([])
    await c.close()
  })

test.beforeAll(() => writeFileSync(REPORT, ''))
