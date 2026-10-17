import { expect, test } from '@playwright/test'
import { PNG as PNG_BYTES } from './flowhelpers'
import { DOC_ID } from './fixtures'
import { PDF, card, consented, pickDrug, reviewReady, setLangInit, watchErrors } from './flowhelpers'
import { mockApi } from './mock'

const png = { name: 'my-private-name.png', mimeType: 'image/png', buffer: PNG_BYTES }

test.describe('consent', () => {
  test('required purposes are shown as required, nothing optional is pre-ticked, and only ticked purposes are sent', async ({ page }) => {
    const mock = await mockApi(page)
    const errors = watchErrors(page)
    await page.goto('/start')
    await page.getByRole('button', { name: 'Begin' }).click()
    await expect(page.getByRole('heading', { level: 1, name: 'Please read and agree' })).toBeFocused()
    const boxes = page.getByRole('checkbox')
    await expect(boxes).toHaveCount(3)
    await expect(boxes.nth(0)).toBeChecked()
    await expect(boxes.nth(0)).toBeDisabled()
    await expect(boxes.nth(2)).not.toBeChecked()
    await expect(page.getByText('Required').first()).toBeVisible()
    await expect(page.getByText('Notice item contact.')).toBeVisible()
    await page.getByRole('button', { name: 'I agree, continue' }).click()
    await expect(page).toHaveURL(/\/upload$/)
    const c = mock.calls.find((x) => x.path === '/api/v1/consent')!
    expect(c.body).toEqual({ notice_version: '2', purposes: ['process_photo', 'store_results_for_session'] })
    expect(mock.calls.every((x) => x.method === 'GET' || x.origin.startsWith('http://localhost:4173'))).toBe(true)
    expect(errors).toEqual([])
  })

  test('the optional photo purpose is sent only when ticked', async ({ page }) => {
    const mock = await mockApi(page, { hasSession: true })
    await page.goto('/consent')
    await page.getByRole('checkbox', { name: /keep the photo/ }).check()
    await page.getByRole('button', { name: 'I agree, continue' }).click()
    await expect(page).toHaveURL(/\/upload$/)
    expect((mock.calls.find((x) => x.path === '/api/v1/consent')!.body as { purposes: string[] }).purposes).toContain('keep_photo_for_session')
  })

  test('a notice version change after loading is reported and the new notice is shown', async ({ page }) => {
    const mock = await mockApi(page, { hasSession: true })
    await page.goto('/consent')
    await expect(page.getByText('Version 2')).toBeVisible()
    mock.setNoticeVersion('3')
    await page.getByRole('button', { name: 'I agree, continue' }).click()
    await expect(page.getByRole('alert')).toContainText('could not be saved')
    await expect(page.getByText('Version 3')).toBeVisible()
    await page.getByRole('button', { name: 'I agree, continue' }).click()
    await expect(page).toHaveURL(/\/upload$/)
  })
})

test.describe('upload', () => {
  test('a PDF is rejected in the browser with the backend wording and nothing is sent', async ({ page }) => {
    const mock = await consented(page)
    await page.goto('/upload')
    await page.locator('#file-pick').setInputFiles({ name: 'x.pdf', mimeType: 'application/pdf', buffer: PDF })
    await expect(page.getByRole('alert')).toContainText('PDF is not supported yet')
    expect(mock.count('POST', '/api/v1/documents')).toBe(0)
  })

  test('a PNG gets an in-memory preview; Choose another resets; Use this photo uploads once with its type', async ({ page }) => {
    const mock = await consented(page)
    await page.goto('/upload')
    await page.locator('#file-pick').setInputFiles(png)
    await expect(page.getByRole('img', { name: 'Preview of the photo you chose' })).toBeVisible()
    expect(await page.locator('.preview img').getAttribute('src')).toMatch(/^blob:/)
    await page.getByRole('button', { name: 'Choose another' }).click()
    await expect(page.getByText('Drop a photo here')).toBeVisible()
    await page.locator('#file-camera').setInputFiles(png)
    await page.getByRole('button', { name: 'Use this photo' }).click()
    await expect(page).toHaveURL(new RegExp(`/d/${DOC_ID}/processing$`))
    expect(mock.count('POST', '/api/v1/documents')).toBe(1)
    expect((mock.calls.find((x) => x.method === 'POST' && x.path === '/api/v1/documents')!.body as { type: string }).type).toBe('image/png')
  })

  test('queue full shows the wait time from Retry-After', async ({ page }) => {
    await consented(page, { fail: { 'POST /api/v1/documents': { status: 429, code: 'queue_full', headers: { 'Retry-After': '60' }, times: 1 } } })
    await page.goto('/upload')
    await page.locator('#file-pick').setInputFiles(png)
    await page.getByRole('button', { name: 'Use this photo' }).click()
    await expect(page.getByRole('alert')).toContainText('about 60 seconds')
    await page.getByRole('button', { name: 'Use this photo' }).click()
    await expect(page).toHaveURL(/processing$/)
  })
})

test.describe('processing', () => {
  test('stages advance, are announced, and the page moves to the review when ready', async ({ page }) => {
    await consented(page, { docSteps: ['queued', 'extracting', 'normalising', 'awaiting_confirmation'] })
    await page.goto('/upload')
    await page.locator('#file-pick').setInputFiles(png)
    await page.getByRole('button', { name: 'Use this photo' }).click()
    await expect(page.getByText('usually takes one to three minutes')).toBeVisible()
    await expect(page.locator('.sr-only[aria-live="polite"]')).toHaveCount(1)
    await expect(page).toHaveURL(/review$/, { timeout: 20_000 })
  })

  for (const [code, text] of [
    ['ollama_unavailable', 'local reader is not running'], ['image_unreadable', 'could not read this photo'], ['context_truncated', 'too long to read'],
    ['image_not_received', 'did not receive the photo'], ['timeout', 'took too long'], ['interrupted', 'interrupted'],
  ] as const) {
    test(`error ${code} shows the backend message with next actions (no retry when the photo was not kept)`, async ({ page }) => {
      await consented(page, { docSteps: ['queued', 'failed'], errorCode: code })
      await page.goto('/upload')
      await page.locator('#file-pick').setInputFiles(png)
      await page.getByRole('button', { name: 'Use this photo' }).click()
      await expect(page.getByText(text, { exact: false }).first()).toBeVisible({ timeout: 15_000 })
      await expect(page.getByRole('link', { name: 'Upload a photo again' })).toBeVisible()
      await expect(page.getByRole('link', { name: 'Return to the start' })).toBeVisible()
      await expect(page.getByRole('button', { name: 'Try reading again' })).toHaveCount(0)
    })
  }

  test('retry is offered only when the photo was kept, and restarts the reading', async ({ page }) => {
    const mock = await mockApi(page, { hasSession: true, consented: true, docSteps: ['queued', 'failed'], errorCode: 'timeout', imageKept: false })
    mock.s.session!.consent.purposes = ['process_photo', 'store_results_for_session', 'keep_photo_for_session']
    await page.goto('/upload')
    await page.locator('#file-pick').setInputFiles(png)
    await page.getByRole('button', { name: 'Use this photo' }).click()
    await page.getByRole('button', { name: 'Try reading again' }).click({ timeout: 15_000 })
    await expect.poll(() => mock.count('POST', /retry$/)).toBe(1)
  })

  test('a reload during processing resumes (no state is held in the browser)', async ({ page }) => {
    await consented(page, { docSteps: ['extracting', 'extracting', 'extracting', 'awaiting_confirmation'] })
    await page.goto('/upload')
    await page.locator('#file-pick').setInputFiles(png)
    await page.getByRole('button', { name: 'Use this photo' }).click()
    await page.reload()
    await expect(page).toHaveURL(/review$/, { timeout: 20_000 })
    await expect(page.getByRole('heading', { level: 1, name: 'Check your medicines' })).toBeVisible()
  })
})

test.describe('review', () => {
  test('clean medicine, garbled name through the picker, acknowledgement, non-daily, and a full-replace save', async ({ page }) => {
    const mock = await reviewReady(page)
    const errors = watchErrors(page)
    await page.goto(`/d/${DOC_ID}/review`)
    await expect(page.getByRole('heading', { level: 1, name: 'Check your medicines' })).toBeFocused()
    await expect(page.getByText('Still to confirm: 2')).toBeVisible()

    // m0: clean, nothing to acknowledge
    await card(page, 0).getByLabel('This matches my document').check()
    await card(page, 0).getByRole('button', { name: 'Use this check' }).click()
    await expect(card(page, 0).getByText('Your check is ready')).toBeVisible()

    // m1: garbled name -> picker; the button waits for the drug, the strength and the acknowledgement
    const c1 = card(page, 1)
    await c1.getByLabel('Choose the right medicine from the list').check()
    await expect(c1.getByRole('button', { name: 'Use this check' })).toBeDisabled()
    await expect(c1.getByText('Compare the brand name, generic name and strength')).toBeVisible()
    await pickDrug(page, c1, 'gly', 'Metformin')
    await expect(c1.getByText('Metformin').first()).toBeVisible()
    await c1.getByLabel('500 mg', { exact: true }).check()
    await expect(c1.getByRole('button', { name: 'Use this check' })).toBeDisabled()
    await c1.getByLabel(/I have checked it on my label/).check()
    await expect(c1.getByRole('button', { name: 'Use this check' })).toBeEnabled()
    await c1.getByRole('button', { name: 'Use this check' }).click()

    // m2: weekly medicine: backend notice, no schedule editor, still needs the acknowledgement
    const c2 = card(page, 2)
    await expect(c2.getByText('not taken every day').first()).toBeVisible()
    await c2.getByLabel('This matches my document').check()
    await expect(c2.getByText('Change how often or when')).toHaveCount(0)
    await c2.getByLabel(/I have checked how often/).check()
    await c2.getByRole('button', { name: 'Use this check' }).click()
    await expect(page.getByText('Still to confirm: 0').or(page.getByText('Every medicine that must be confirmed has your check.'))).toBeVisible()

    // add a medicine from the picker (no free text), fixed dose list
    await page.getByRole('button', { name: 'Add a medicine I do not see here' }).click()
    const add = page.locator('.add-med')
    await pickDrug(page, add, 'omep', 'Omeprazole')
    await add.getByLabel('20 mg', { exact: true }).check()
    await add.getByLabel('Dose').selectOption('1 capsule')
    await add.getByLabel('Times per day').selectOption('1')
    await add.getByLabel('When').selectOption('before_meals')
    await add.getByRole('button', { name: 'Add to my list' }).click()
    await expect(page.getByText('You added this medicine from the list.')).toBeVisible()

    await page.getByRole('button', { name: 'Save my checks' }).click()
    await expect(page.getByRole('heading', { name: 'Your checks are saved' })).toBeVisible()
    const body = mock.calls.filter((x) => x.path.endsWith('/confirmations')).at(-1)!.body as { decisions: { index: number; action: string; formulary_id?: string; acknowledged_flags?: string[] }[]; added_medicines: { formulary_id: string; dose: string }[] }
    expect(body.decisions.map((d) => [d.index, d.action])).toEqual([[0, 'confirm_as_extracted'], [1, 'select_formulary_drug'], [2, 'confirm_as_extracted']])
    expect(body.decisions[1]).toMatchObject({ formulary_id: 'metformin', strength_choice: '500 mg', acknowledged_flags: ['unusual_strength'] })
    expect(body.decisions[2].acknowledged_flags).toEqual(['non_daily_frequency'])
    expect(body.added_medicines[0]).toMatchObject({ formulary_id: 'omeprazole', dose: '1 capsule', schedule: { times_per_day: 1, timing_label: 'before_meals', duration_days: null } })
    expect(errors).toEqual([])

    // reload restores the saved decisions from the server and a second save REPLACES the set (everything is sent again)
    await page.reload()
    await expect(card(page, 1).getByText('Your check is ready')).toBeVisible()
    await expect(page.getByText('You added this medicine from the list.')).toBeVisible()
    await card(page, 3).getByLabel('My medicine is not in the list').check()
    await card(page, 3).getByRole('button', { name: 'Mark as not in the list' }).click()
    await page.getByRole('button', { name: 'Save my checks' }).click()
    await expect(page.getByRole('heading', { name: 'Your checks are saved' })).toBeVisible()
    const again = mock.calls.filter((x) => x.path.endsWith('/confirmations')).at(-1)!.body as { decisions: unknown[]; added_medicines: unknown[] }
    expect(again.decisions).toHaveLength(4)
    expect(again.added_medicines).toHaveLength(1)
  })

  test('not in list: note limited to 80 characters with a counter; remove needs no acknowledgement', async ({ page }) => {
    const mock = await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    const c = card(page, 1)
    await c.getByLabel('My medicine is not in the list').check()
    await c.getByLabel(/Note/).fill('x'.repeat(120))
    await expect(c.getByText('80 of 80 characters.')).toBeVisible()
    await expect(c.getByText('do not enter names')).toBeVisible()
    await c.getByRole('button', { name: 'Mark as not in the list' }).click()
    const r = card(page, 2)
    await r.getByLabel(/Remove: this is not on my document/).check()
    await expect(r.getByRole('button', { name: 'Remove this medicine' })).toBeEnabled()
    await r.getByRole('button', { name: 'Remove this medicine' }).click()
    await page.getByRole('button', { name: 'Save my checks' }).click()
    await expect(page.getByRole('heading', { name: 'Your checks are saved' })).toBeVisible()
    const b = mock.calls.filter((x) => x.path.endsWith('/confirmations')).at(-1)!.body as { decisions: { index: number; action: string; note?: string }[] }
    expect(b.decisions).toEqual([{ index: 1, action: 'not_in_list', note: 'x'.repeat(80) }, { index: 2, action: 'remove' }])
  })

  test('the picker is a keyboard-operable combobox (ARIA roles, Escape closes, nothing preselected)', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    const c = card(page, 1)
    await c.getByLabel('Choose the right medicine from the list').check()
    const box = c.getByRole('combobox', { name: /Search medicine/ })
    await expect(box).toHaveAttribute('aria-autocomplete', 'list')
    await expect(box).toHaveValue('')
    await box.fill('p')
    await expect(c.getByRole('listbox')).toBeVisible()
    await expect(box).toHaveAttribute('aria-expanded', 'true')
    await box.press('ArrowDown')
    await expect(box).toHaveAttribute('aria-activedescendant', /opt-0/)
    await box.press('Escape')
    await expect(box).toHaveAttribute('aria-expanded', 'false')
    await expect(c.locator('.picked')).toHaveCount(0) // nothing chosen
  })

  test('unsaved decisions ask before leaving; staying keeps them', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    await card(page, 1).getByLabel('Remove: this is not on my document').check()
    await card(page, 1).getByRole('button', { name: 'Remove this medicine' }).click()
    await page.getByRole('link', { name: 'See results' }).click()
    const dlg = page.getByRole('dialog', { name: 'Leave without saving?' })
    await expect(dlg).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(dlg).toBeHidden()
    await expect(page).toHaveURL(/review$/)
    await page.getByRole('link', { name: 'See results' }).click()
    await page.getByRole('button', { name: 'Leave without saving' }).click()
    await expect(page).toHaveURL(/result$/)
  })

  test('the photo (from the upload, memory only) sits beside the list; without it the page says so', async ({ page }) => {
    await consented(page, { docSteps: ['awaiting_confirmation'] })
    await page.goto('/upload')
    await page.locator('#file-pick').setInputFiles(png)
    await page.getByRole('button', { name: 'Use this photo' }).click()
    await expect(page).toHaveURL(/review$/, { timeout: 15_000 })
    await expect(page.locator('.pv-frame img')).toHaveAttribute('src', /^blob:/)
    await page.locator('.pv-frame').focus()
    await page.keyboard.press('+')
    await expect(page.locator('.pv-frame img')).toHaveAttribute('style', /scale\(1\.5\)/)
    await page.reload() // not kept: the preview is gone
    await expect(page.getByText('hold your paper document next to the screen')).toBeVisible()
  })
})

test.describe('results', () => {
  test('confirm-first before the check, interaction card after; ta tab prepares then shows lines with draft chips', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/result`)
    await expect(page.getByRole('heading', { level: 1, name: 'Your results' })).toBeFocused()
    await expect(page.getByText('Confirm first', { exact: true })).toBeVisible()
    await expect(page.getByText('This does not mean they are safe.')).toBeVisible()
    await expect(page.getByText('Please check this medicine against your document')).toBeVisible()
    await page.getByRole('tab', { name: 'தமிழ்' }).click()
    await expect(page.getByText('Still preparing this explanation')).toBeVisible()
    await expect(page.getByText('நிறைய தண்ணீர் குடியுங்கள்.')).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText('Automatic translation checked by software only').first()).toBeVisible()
  })

  test('after confirmation: the interaction is its own card with level icon and text, source label and one aggregated not-checked line', async ({ page }) => {
    await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/review`)
    await card(page, 1).getByLabel('Remove: this is not on my document').check()
    await card(page, 1).getByRole('button', { name: 'Remove this medicine' }).click()
    await page.getByRole('button', { name: 'Save my checks' }).click()
    await page.getByRole('link', { name: 'See results' }).click()
    await expect(page.getByText('Confirm first', { exact: true })).toHaveCount(0)
    const pair = page.locator('.pair-card')
    await expect(pair).toHaveCount(1)
    await expect(pair.getByText('Moderate interaction found')).toBeVisible()
    await expect(pair.getByText('DDInter database')).toBeVisible()
    await expect(page.getByText('We could not check 5 pairs')).toHaveCount(1)
    await expect(page.getByRole('button', { name: 'Print or save as PDF' })).toBeVisible()
  })

  test('a failed narrative shows the original text with the fallback notice and chip', async ({ page }) => {
    await reviewReady(page, { narrativeFinal: 'failed' })
    await page.goto(`/d/${DOC_ID}/result`)
    await page.getByRole('tab', { name: 'हिन्दी' }).click()
    await expect(page.getByText('Original text from your document', { exact: true })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText('could not be checked in your language')).toBeVisible()
  })
})

test.describe('schedule, summary and deletion', () => {
  test('mark taken and skipped, undo, edit times, no reminders statement; summary counts; print stylesheet hides navigation', async ({ page }) => {
    const mock = await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/schedule`)
    await expect(page.getByText('sends no reminders')).toBeVisible()
    await expect(page.getByText('does not ask for your browser')).toBeVisible()
    await expect(page.getByText("Suggested times only; adjust them to match your doctor's instructions.")).toBeVisible()
    await expect(page.getByText('Not scheduled: this medicine is not taken every day')).toBeVisible()
    const first = page.locator('.slot').nth(1) // 08:30
    await first.getByRole('button', { name: 'Taken' }).click()
    await expect(first.getByRole('button', { name: 'Taken' })).toHaveAttribute('aria-pressed', 'true')
    await page.locator('.slot').nth(2).getByRole('button', { name: 'Skipped' }).click()
    expect(mock.s.events.map((e) => e.status).sort()).toEqual(['skipped', 'taken'])
    await first.getByRole('button', { name: 'Undo' }).click()
    await expect.poll(() => mock.s.events.length).toBe(1)
    await page.getByRole('button', { name: 'Change times' }).first().click()
    await page.getByRole('textbox', { name: 'Time 1' }).fill('09:15')
    await page.getByRole('button', { name: 'Save times' }).click()
    await expect(page.getByText('09:15').first()).toBeVisible()
    expect(mock.s.overrides).toEqual({ m0: ['09:15', '20:30'] })
    // invalid times are refused in the browser
    await page.getByRole('button', { name: 'Change times' }).first().click()
    await page.getByRole('textbox', { name: 'Time 1' }).fill('')
    await page.getByRole('button', { name: 'Save times' }).click()
    await expect(page.getByRole('alert')).toContainText('one to six different times')

    await page.getByRole('link', { name: 'Summary for my doctor' }).click()
    await expect(page.getByRole('heading', { level: 1, name: 'Summary to show your doctor' })).toBeVisible()
    await expect(page.getByRole('row', { name: /Glycomet/ })).toBeVisible()
    await expect(page.getByText('It may contain mistakes.')).toBeVisible()
    await expect(page.locator('main').getByText(/%/)).toHaveCount(0) // counts only, no percentages
    await page.emulateMedia({ media: 'print' })
    await expect(page.locator('.site-header')).toBeHidden()
    await expect(page.locator('.range')).toBeHidden()
  })

  test('delete my data: dialog with consequences, Escape closes, confirm erases, receipt shown on the landing page, state cleared', async ({ page }) => {
    const mock = await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/result`)
    await page.getByRole('button', { name: 'Delete my data' }).click()
    const dlg = page.getByRole('dialog', { name: 'Delete everything for this session?' })
    await expect(dlg).toContainText('cannot be undone')
    await expect(dlg.getByRole('button', { name: 'Keep my data' })).toBeFocused()
    await page.keyboard.press('Escape')
    await expect(dlg).toBeHidden()
    await page.getByRole('button', { name: 'Delete my data' }).click()
    await dlg.getByRole('button', { name: 'Delete everything' }).click()
    await expect(page).toHaveURL(/\/$/)
    await expect(page.getByText('Your data has been deleted and your consent is withdrawn.')).toBeVisible()
    await expect(page.getByText(/Deleted: 1 documents/)).toBeVisible()
    expect(mock.s.session).toBeNull()
    await expect(page.getByRole('button', { name: 'Delete my data' })).toHaveCount(0)
    await page.goto(`/d/${DOC_ID}/result`) // everything is gone: back to the start
    await expect(page).toHaveURL(/\/start$/)
  })

  test('documents list says deleting removes everything for the session', async ({ page }) => {
    await reviewReady(page)
    await page.goto('/documents')
    await expect(page.getByText('Ready for your check')).toBeVisible()
    await expect(page.getByText('A single document cannot be deleted on its own.')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Delete everything, including these documents' })).toBeVisible()
  })
})

test.describe('session problems', () => {
  test('401 in the middle of the flow explains expiry and offers to start again', async ({ page }) => {
    const mock = await reviewReady(page)
    await page.goto(`/d/${DOC_ID}/schedule`)
    await expect(page.locator('.slot').first()).toBeVisible()
    mock.expire()
    await page.locator('.slot').first().getByRole('button', { name: 'Taken' }).click()
    await expect(page.getByText('Your session has ended', { exact: true })).toBeVisible()
    await page.getByRole('button', { name: 'Start again' }).click()
    await expect(page).toHaveURL(/\/start$/)
  })

  test('403 consent_required sends the person to the consent step', async ({ page }) => {
    await reviewReady(page, { fail: { 'GET /api/v1/documents/{doc_id}/medicines': { status: 403, code: 'consent_required', times: 1 } } })
    await page.goto(`/d/${DOC_ID}/review`)
    await expect(page).toHaveURL(/\/consent$/)
  })

  test('backend unreachable on a flow page: clear message and retry', async ({ page }) => {
    await page.route('**/api/**', (r) => r.abort())
    await page.goto('/upload')
    await expect(page.getByText('The server is not reachable')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible()
  })
})

test.describe('audits after a full flow', () => {
  test('nothing about the document is stored in the browser, no external request, no console error', async ({ page, context }) => {
    const mock = await consented(page, { docSteps: ['queued', 'awaiting_confirmation'] })
    const errors = watchErrors(page)
    const hosts = new Set<string>()
    page.on('request', (r) => hosts.add(new URL(r.url()).host))
    await setLangInit(page, 'en')
    await page.goto('/upload')
    await page.locator('#file-pick').setInputFiles(png)
    await page.getByRole('button', { name: 'Use this photo' }).click()
    await expect(page).toHaveURL(/review$/, { timeout: 15_000 })
    await card(page, 1).getByLabel('Choose the right medicine from the list').check()
    await pickDrug(page, card(page, 1), 'gly', 'Metformin')
    await card(page, 1).getByLabel('500 mg', { exact: true }).check()
    await card(page, 1).getByLabel(/I have checked it on my label/).check()
    await card(page, 1).getByRole('button', { name: 'Use this check' }).click()
    await page.getByRole('button', { name: 'Save my checks' }).click()
    await page.getByRole('link', { name: 'See results' }).click()
    await expect(page.locator('.pair-card')).toHaveCount(1)
    await page.goto(`/d/${DOC_ID}/schedule`)
    await page.locator('.slot').first().getByRole('button', { name: 'Taken' }).click()
    await page.goto(`/d/${DOC_ID}/summary`)
    await expect(page.getByRole('row', { name: /Glycomet/ })).toBeVisible()

    const audit = await page.evaluate(async () => ({
      local: Object.keys(localStorage), session: Object.keys(sessionStorage), cookie: document.cookie, search: location.search, hash: location.hash, title: document.title, state: history.state,
      idb: indexedDB.databases ? (await indexedDB.databases()).length : 0, caches: 'caches' in window ? (await caches.keys()).length : 0,
    }))
    expect(audit.local.filter((k) => !['carebridge.language', 'carebridge.calm'].includes(k))).toEqual([])
    expect(audit).toMatchObject({ session: [], cookie: '', search: '', hash: '', idb: 0, caches: 0 })
    expect(audit.title).not.toMatch(/Glycomet|Netfornin|Metformin|Vm6V|my-private-name/)
    expect(JSON.stringify(audit.state)).not.toMatch(/Vm6V|Glycomet|Metformin/)
    expect(await context.cookies()).toEqual([]) // the frontend sets no cookies (the real session cookie is HttpOnly and set by the backend)
    expect([...hosts]).toEqual(['localhost:4173'])
    expect(errors).toEqual([])
    expect(mock.calls.some((c) => c.path.includes('?') && /Glycomet|Netfornin/.test(c.path))).toBe(false)
  })

  test('reduced motion and calm mode: no animated bar, no particles on a processing screen', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await consented(page, { docSteps: ['extracting'] })
    await page.goto('/upload')
    await page.locator('#file-pick').setInputFiles(png)
    await page.getByRole('button', { name: 'Use this photo' }).click()
    await expect(page.getByRole('progressbar')).toBeVisible()
    expect(await page.locator('.busy-bar span').evaluate((e) => getComputedStyle(e).animationName)).toBe('none')
    await page.getByRole('button', { name: /Calm mode/ }).click()
    await expect(page.locator('html')).toHaveClass(/calm/)
  })

  test('the landing page still works when the backend is unreachable', async ({ page }) => {
    await page.route('**/api/**', (r) => r.abort())
    const errors = watchErrors(page)
    await page.goto('/')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    expect(errors).toEqual([])
  })
})

test.describe('reload restores every stage from the server', () => {
  for (const [route, h1] of [['/documents', 'Documents in this session'], ['/review', 'Check your medicines'], ['/result', 'Your results'], ['/schedule', 'Your schedule'], ['/summary', 'Summary to show your doctor']] as const)
    test(`reload on ${route}`, async ({ page }) => {
      await reviewReady(page)
      const errors = watchErrors(page)
      await page.goto(route === '/documents' ? route : `/d/${DOC_ID}${route}`)
      await expect(page.getByRole('heading', { level: 1, name: h1 })).toBeVisible()
      await page.reload()
      await expect(page.getByRole('heading', { level: 1, name: h1 })).toBeVisible()
      expect(errors).toEqual([])
    })
  test('reload on /consent and /upload keeps the session', async ({ page }) => {
    await consented(page)
    await page.goto('/upload')
    await page.reload()
    await expect(page.getByRole('heading', { level: 1, name: 'Add a photo of your document' })).toBeVisible()
  })
})
