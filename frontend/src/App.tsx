import { Route, Routes } from 'react-router-dom'
import { Shell } from './layout/Shell'
import { HowItWorksPage } from './pages/HowItWorksPage'
import { LandingPage } from './pages/LandingPage'
import { PrivacyPage } from './pages/PrivacyPage'
import { NotFoundPage, StartPage } from './pages/SimplePages'

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<LandingPage />} />
        <Route path="start" element={<StartPage />} />
        <Route path="privacy" element={<PrivacyPage />} />
        <Route path="how-it-works" element={<HowItWorksPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
