import type { RouteObject } from 'react-router-dom'
import { SampleOnlyPage } from './pages/SampleOnlyPage'

/** Hosted sample build: every real-flow route shows the "sample only" page. No page that talks to the backend is imported here. */
export const realRoutes: RouteObject[] = ['start', 'consent', 'upload', 'documents', 'd/*'].map((path) => ({ path, element: <SampleOnlyPage /> }))
