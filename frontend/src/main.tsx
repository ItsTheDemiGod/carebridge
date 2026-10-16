import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { MotionProvider } from './ambient/motion'
import { I18nProvider } from './i18n/I18n'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <I18nProvider>
        <MotionProvider>
          <App />
        </MotionProvider>
      </I18nProvider>
    </BrowserRouter>
  </StrictMode>,
)
