import { useLocation, useParams } from 'react-router-dom'
import { DEMO_ID, isDemoPath } from './demoApi'

export const useIsDemo = () => isDemoPath(useLocation().pathname)

/** The document id of the current flow page: from the route, or the fixed sample id under /demo. */
export function useDocId(): string {
  const { id } = useParams()
  return useIsDemo() ? DEMO_ID : (id ?? '')
}

/** Where the pages of one document live: /d/:id/<page> in the real flow, /demo/<page> in the sample. */
export type DocPage = 'processing' | 'review' | 'result' | 'schedule' | 'summary'
export function useDocPath(): (id: string, page: DocPage) => string {
  const demo = useIsDemo()
  return (id, page) => (demo ? `/demo/${page}` : `/d/${id}/${page}`)
}
