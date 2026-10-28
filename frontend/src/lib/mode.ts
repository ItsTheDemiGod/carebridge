import links from '../data/links.json'

/* Build mode and base path (Phase 8a). DEMO_ONLY is a build-time constant (vite define): the hosted GitHub Pages site contains only the public pages and the pre-recorded
 * sample, never the real flow. BASE is "/" for the normal build and "/carebridge/" for the Pages build. */
export const DEMO_ONLY: boolean = import.meta.env.VITE_DEMO_ONLY === '1'
export const BASE: string = import.meta.env.BASE_URL

/** A browser pathname without the base path ("/carebridge/demo/review" -> "/demo/review"). */
export const stripBase = (p: string, base: string = BASE) => (base !== '/' && (p === base.slice(0, -1) || p.startsWith(base)) ? p.slice(base.length - 1) || '/' : p)
/** A public file under the base path ("demo/x.png" or "/demo/x.png" -> "/carebridge/demo/x.png"). */
export const withBase = (p: string, base: string = BASE) => base + p.replace(/^\//, '')

/** The public project repository (a link target kept in data, like the photo credits; the app makes no request to it). */
export const REPO_URL: string = links.repository
