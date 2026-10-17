import type { RouteObject } from 'react-router-dom'
import { Shell } from './layout/Shell'
import { HowItWorksPage } from './pages/HowItWorksPage'
import { LandingPage } from './pages/LandingPage'
import { PrivacyPage } from './pages/PrivacyPage'
import { ConsentPage } from './pages/flow/ConsentPage'
import { ProcessingPage } from './pages/flow/ProcessingPage'
import { StartPage } from './pages/flow/StartPage'
import { UploadPage } from './pages/flow/UploadPage'
import { NotFoundPage } from './pages/SimplePages'

export const routes: RouteObject[] = [
  {
    element: <Shell />,
    children: [
      { index: true, element: <LandingPage /> },
      { path: 'start', element: <StartPage /> },
      { path: 'consent', element: <ConsentPage /> },
      { path: 'upload', element: <UploadPage /> },
      { path: 'd/:id/processing', element: <ProcessingPage /> },
      { path: 'privacy', element: <PrivacyPage /> },
      { path: 'how-it-works', element: <HowItWorksPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
