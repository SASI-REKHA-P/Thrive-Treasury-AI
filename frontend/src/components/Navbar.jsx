import { useState, useEffect } from 'react'
import { Sun, Moon, Menu, X, ArrowRight, ShieldCheck } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export default function Navbar() {
  const { theme, toggleTheme } = useTheme()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const closeMobileMenu = () => setMobileMenuOpen(false)

  return (
    <header className={`navbar-header ${scrolled ? 'scrolled' : ''}`}>
      <div className="navbar-container">
        {/* Brand Emblem */}
        <a href="#" className="navbar-brand" onClick={closeMobileMenu}>
          <div className="brand-icon-wrapper">
            <ShieldCheck className="brand-icon" size={22} />
          </div>
          <span className="brand-name">
            Thrive <span className="brand-highlight">Treasury AI</span>
          </span>
        </a>

        {/* Desktop Navigation Links */}
        <nav className="navbar-links" aria-label="Main Navigation">
          <a href="#architecture" className="nav-link">Architecture</a>
          <a href="#why-thrive" className="nav-link">Principles</a>
        </nav>

        {/* Right Actions: Theme Toggle & Get Started */}
        <div className="navbar-actions">
          <button
            type="button"
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          >
            {theme === 'dark' ? (
              <Sun size={18} className="theme-icon sun" />
            ) : (
              <Moon size={18} className="theme-icon moon" />
            )}
          </button>

          <a href="/app" className="btn-get-started desktop-only">
            <span>Get Started</span>
            <ArrowRight size={16} />
          </a>

          {/* Mobile Menu Toggle */}
          <button
            type="button"
            className="mobile-menu-toggle"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="mobile-drawer" role="dialog" aria-modal="true">
          <nav className="mobile-nav-links">
            <a href="#architecture" className="mobile-nav-link" onClick={closeMobileMenu}>
              Architecture
            </a>
            <a href="#why-thrive" className="mobile-nav-link" onClick={closeMobileMenu}>
              Principles
            </a>
            <a href="/app" className="btn-get-started mobile-cta" onClick={closeMobileMenu}>
              <span>Get Started</span>
              <ArrowRight size={16} />
            </a>
          </nav>
        </div>
      )}
    </header>
  )
}
