import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider, createBrowserRouter } from 'react-router-dom'
import './index.css'
import { routes } from './App.tsx'
import { MotionProvider } from './ambient/motion'
import { I18nProvider } from './i18n/I18n'

const router = createBrowserRouter(routes)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <I18nProvider>
      <MotionProvider>
        <RouterProvider router={router} />
      </MotionProvider>
    </I18nProvider>
  </StrictMode>,
)
