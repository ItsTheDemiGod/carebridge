import type { RouteObject } from 'react-router-dom'
import { Shell } from './layout/Shell'
import { HowItWorksPage } from './pages/HowItWorksPage'
import { LandingPage } from './pages/LandingPage'
import { PrivacyPage } from './pages/PrivacyPage'
import { ConsentPage } from './pages/flow/ConsentPage'
import { ProcessingPage } from './pages/flow/ProcessingPage'
import { ResultPage } from './pages/flow/ResultPage'
import { ReviewPage } from './pages/flow/ReviewPage'
import { SchedulePage } from './pages/flow/SchedulePage'
import { StartPage } from './pages/flow/StartPage'
import { SummaryPage } from './pages/flow/SummaryPage'
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
      { path: 'd/:id/review', element: <ReviewPage /> },
      { path: 'd/:id/result', element: <ResultPage /> },
      { path: 'd/:id/schedule', element: <SchedulePage /> },
      { path: 'd/:id/summary', element: <SummaryPage /> },
      { path: 'privacy', element: <PrivacyPage /> },
      { path: 'how-it-works', element: <HowItWorksPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
