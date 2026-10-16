import { useState, type CSSProperties, type ReactNode } from 'react'
import manifest from '../photos.manifest.json'
import { Icon } from './icons'

type Entry = { width: number; height: number; widths: number[]; credit?: string }
const MAN = manifest as Record<string, Entry>

type PhotoProps = {
  name: string // base file name written by scripts/prepare_photos.py, e.g. "pillbox"
  alt: string // required; pass "" only for purely decorative photographs
  missingLabel: string // shown on the designed placeholder when the file is not there
  sizes?: string
  eager?: boolean
  className?: string
  duotone?: boolean
}

/** Photograph with a CSS duotone (pine and paper), lazy loading and explicit width and height. When the file is
 *  missing (not in the manifest, or fails to load) a designed placeholder tile is shown instead. */
export function Photo({ name, alt, missingLabel, sizes = '(min-width: 64rem) 40vw, 100vw', eager, className = '', duotone = true }: PhotoProps) {
  const [failed, setFailed] = useState(false)
  const e = MAN[name]
  if (!e || failed) {
    return (
      <div className={`photo photo-missing ${className}`.trim()} role={alt ? 'img' : undefined} aria-label={alt || undefined} aria-hidden={alt ? undefined : true}>
        <Icon name="leaf" size={40} />
        {missingLabel ? <span className="photo-missing-label">{missingLabel}</span> : null}
      </div>
    )
  }
  const set = (ext: string) => e.widths.map((w) => `/photos/${name}-${w}.${ext} ${w}w`).join(', ')
  return (
    <div className={`photo ${duotone ? 'photo-duotone' : ''} ${className}`.trim()} style={{ aspectRatio: `${e.width} / ${e.height}` } as CSSProperties}>
      <picture>
        <source type="image/webp" srcSet={set('webp')} sizes={sizes} />
        <img src={`/photos/${name}-${e.widths[Math.min(1, e.widths.length - 1)]}.jpg`} srcSet={set('jpg')} sizes={sizes} width={e.width} height={e.height} alt={alt} loading={eager ? 'eager' : 'lazy'} decoding="async" onError={() => setFailed(true)} />
      </picture>
    </div>
  )
}

export type TileTone = 'pine' | 'sage' | 'mist' | 'paper' | 'terracotta' | 'ink'
export type TilePattern = 'none' | 'lines' | 'dots' | 'arches' | 'grain'

/** A rounded mosaic tile: solid colour with an optional line pattern or grain; children (photo, icon) sit inside. */
export function Tile({ tone = 'mist', pattern = 'none', children, className = '', style }: { tone?: TileTone; pattern?: TilePattern; children?: ReactNode; className?: string; style?: CSSProperties }) {
  return (
    <div className={`tile tile-${tone} tile-p-${pattern} ${className}`.trim()} style={style}>
      {children}
    </div>
  )
}
