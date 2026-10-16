import { useRef } from 'react'
import { useParallax } from '../ambient/useParallax'
import { Notice, Tag } from '../components/Badges'
import { ButtonLink, TextLink } from '../components/Button'
import { ConfirmFigure } from '../components/ConfirmFigure'
import { Icon, type IconName } from '../components/icons'
import { Container, Rule, SectionHeading } from '../components/Layout'
import { Mosaic } from '../components/Mosaic'
import { Photo } from '../components/Photo'
import { Reveal } from '../components/Reveal'
import { useT } from '../i18n/I18n'
import { LANGS, STRINGS, translate } from '../i18n/translate'
import { usePageTitle } from './usePageTitle'

const STEPS: { n: '1' | '2' | '3'; icon: IconName }[] = [
  { n: '1', icon: 'camera' },
  { n: '2', icon: 'search' },
  { n: '3', icon: 'document' },
]
const PRIVACY: { id: 'local' | 'stored' | 'delete'; icon: IconName }[] = [
  { id: 'local', icon: 'lock' },
  { id: 'stored', icon: 'clock' },
  { id: 'delete', icon: 'trash' },
]
const LIMITS = ['1', '2', '3', '4', '5', '6'] as const

export function LandingPage() {
  const { t } = useT()
  usePageTitle('ui.title.home')
  const root = useRef<HTMLDivElement>(null)
  useParallax(root)

  return (
    <div ref={root} className="landing">
      {/* 1 hero */}
      <Container as="section" className="hero">
        <div className="hero-copy">
          <p className="label">{t('ui.hero.eyebrow')}</p>
          <h1 className="display">{t('ui.hero.title')}</h1>
          <p className="lede">{t('ui.hero.sub')}</p>
          <div className="hero-actions">
            <ButtonLink to="/start" icon="arrow">
              {t('ui.hero.cta')}
            </ButtonLink>
            <ButtonLink to="/how-it-works" variant="quiet">
              {t('ui.hero.link')}
            </ButtonLink>
          </div>
          <p className="hero-note small muted">{t('ui.hero.note')}</p>
        </div>
        <div className="hero-art">
          <Mosaic />
        </div>
      </Container>

      <Container>
        <ul className="meta-strip">
          <li><Icon name="lock" size={20} />{t('ui.privacy.local.title')}</li>
          <li><Icon name="trash" size={20} />{t('ui.privacy.delete.title')}</li>
          <li><Icon name="info" size={20} />{t('ui.hero.note')}</li>
        </ul>
      </Container>

      {/* 2 steps */}
      <Container as="section" className="steps section" aria-labelledby="steps-title">
        <SectionHeading number="01" label={t('ui.steps.label')} title={t('ui.steps.title')} id="steps-title" />
        <div className="steps-body">
          <div className="steps-photo" data-parallax="0.06">
            <Photo name="blister" alt={t('ui.photo.blister')} missingLabel={t('ui.photo.missing')} sizes="(min-width: 64rem) 30vw, 90vw" />
          </div>
          <ol className="steps-list">
            {STEPS.map(({ n, icon }) => (
              <Reveal as="li" key={n} delay={Number(n) * 90}>
                <span className="step-num" aria-hidden="true">{`0${n}`}</span>
                <div>
                  <h3><Icon name={icon} size={26} />{t(`ui.steps.${n}.title`)}</h3>
                  <p>{t(`ui.steps.${n}.body`)}</p>
                </div>
              </Reveal>
            ))}
          </ol>
        </div>
      </Container>

      {/* 3 confirm first */}
      <section id="confirm" className="confirm band-paper2 section" aria-labelledby="confirm-title">
        <Container className="confirm-grid">
          <div>
            <SectionHeading number="02" label={t('ui.confirm.label')} title={t('ui.confirm.title')} id="confirm-title" />
            <div className="stack">
              <p>{t('ui.confirm.body1')}</p>
              <p>{t('ui.confirm.body2')}</p>
              <p>{t('ui.confirm.body3')}</p>
            </div>
          </div>
          <Reveal className="confirm-art">
            <div data-parallax="0.03">
              <ConfirmFigure />
            </div>
          </Reveal>
        </Container>
      </section>

      {/* 4 languages */}
      <Container as="section" className="section" aria-labelledby="lang-title">
        <SectionHeading number="03" label={t('ui.langblock.label')} title={t('ui.langblock.title')} id="lang-title" />
        <p className="lede">{t('ui.langblock.body')}</p>
        <ul className="lang-rows">
          {LANGS.map((l) => {
            const draft = STRINGS[l.code]['ui.sample.line'].review_status !== 'not_required'
            return (
              <Reveal as="li" key={l.code}>
                <span className="lang-name" lang={l.code}>{l.name}</span>
                <p className="lang-sample" lang={l.code}>{translate(l.code, 'ui.sample.line')}</p>
                <Tag tone={draft ? 'draft' : 'accent'} icon={draft ? 'info' : 'check'}>
                  {draft ? t('ui.langblock.chip_draft') : t('ui.langblock.chip_en')}
                </Tag>
              </Reveal>
            )
          })}
        </ul>
      </Container>

      {/* 5 privacy */}
      <section className="privacy-band on-dark section" aria-labelledby="privacy-title">
        <Container className="privacy-grid">
          <div>
            <p className="label on-dark-label"><span className="label-num">04</span><span>{t('ui.privacy.label')}</span></p>
            <h2 id="privacy-title">{t('ui.privacy.title')}</h2>
            <p className="privacy-link"><TextLink to="/privacy">{t('ui.privacy.link')}</TextLink></p>
          </div>
          <ul className="privacy-list">
            {PRIVACY.map(({ id, icon }) => (
              <Reveal as="li" key={id}>
                <Icon name={icon} size={32} />
                <div>
                  <h3>{t(`ui.privacy.${id}.title`)}</h3>
                  <p>{t(`ui.privacy.${id}.body`)}</p>
                </div>
              </Reveal>
            ))}
          </ul>
        </Container>
      </section>

      {/* 6 limits */}
      <Container as="section" className="section" id="limits" aria-labelledby="limits-title">
        <Notice tone="important">
          <p className="label"><span className="label-num">05</span><span>{t('ui.limits.label')}</span></p>
          <h2 id="limits-title" className="limits-title">{t('ui.limits.title')}</h2>
          <ol className="limits-list">
            {LIMITS.map((n) => (
              <li key={n}>{t(`ui.limits.${n}`)}</li>
            ))}
          </ol>
        </Notice>
      </Container>

      {/* 7 testing teaser */}
      <Container as="section" className="testing" id="testing" aria-labelledby="testing-title">
        <Rule />
        <div className="testing-row">
          <p className="label"><span className="label-num">06</span><span>{t('ui.testing.label')}</span></p>
          <h2 id="testing-title" className="h3-like">{t('ui.testing.title')}</h2>
          <p>{t('ui.testing.body')}</p>
          <p id="testing-notes"><TextLink to="#testing-notes">{t('ui.testing.link')}</TextLink></p>
        </div>
      </Container>
    </div>
  )
}
