import { useState, useEffect } from 'react'
import { ThemeProvider } from './context/ThemeContext'
import Navbar from './components/Navbar'
import Hero from './components/Hero'
import ArchitecturePipeline from './components/ArchitecturePipeline'
import WhyThrive from './components/WhyThrive'
import FinalCta from './components/FinalCta'
import Footer from './components/Footer'
import FinanceControllerDashboard from './components/dashboard/FinanceControllerDashboard'
import './App.css'

function App() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname)

  useEffect(() => {
    const handleLocationChange = () => {
      setCurrentPath(window.location.pathname)
    }

    // Intercept client-side link navigation for smooth routing between "/" and "/app"
    const handleLinkClick = (e) => {
      const anchor = e.target.closest('a')
      if (anchor) {
        const href = anchor.getAttribute('href')
        if (href === '/app' || href === '/') {
          e.preventDefault()
          window.history.pushState({}, '', href)
          setCurrentPath(href)
          window.scrollTo(0, 0)
        }
      }
    }

    window.addEventListener('popstate', handleLocationChange)
    document.addEventListener('click', handleLinkClick)

    return () => {
      window.removeEventListener('popstate', handleLocationChange)
      document.removeEventListener('click', handleLinkClick)
    }
  }, [])

  // Mount Finance Controller Dashboard at /app
  if (currentPath === '/app') {
    return (
      <ThemeProvider>
        <FinanceControllerDashboard
          onNavigateHome={() => {
            window.history.pushState({}, '', '/')
            setCurrentPath('/')
            window.scrollTo(0, 0)
          }}
        />
      </ThemeProvider>
    )
  }


  // Public Landing Page (Feature 1 - Interactive Architecture Pipeline)
  return (
    <ThemeProvider>
      <div className="landing-page-wrapper">
        <Navbar />
        <main>
          <Hero />
          <ArchitecturePipeline />
          <WhyThrive />
          <FinalCta />
        </main>
        <Footer />
      </div>
    </ThemeProvider>
  )
}

export default App
