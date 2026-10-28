import type { RouteObject } from 'react-router-dom'
import { ConsentPage } from './pages/flow/ConsentPage'
import { DocumentsPage } from './pages/flow/DocumentsPage'
import { ProcessingPage } from './pages/flow/ProcessingPage'
import { StartPage } from './pages/flow/StartPage'
import { UploadPage } from './pages/flow/UploadPage'

/** The routes that need the backend. The hosted sample build (vite --mode pages) swaps this module for routes.real.stub.tsx, so none of these pages is bundled there. */
export const realRoutes: RouteObject[] = [
  { path: 'start', element: <StartPage /> },
  { path: 'consent', element: <ConsentPage /> },
  { path: 'upload', element: <UploadPage /> },
  { path: 'd/:id/processing', element: <ProcessingPage /> },
  { path: 'documents', element: <DocumentsPage /> },
]
