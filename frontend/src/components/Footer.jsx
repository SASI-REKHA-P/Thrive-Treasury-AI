import { ShieldCheck } from 'lucide-react'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="footer-main">
      <div className="footer-container">
        <div className="footer-top">
          {/* Brand Info */}
          <div className="footer-brand-col">
            <div className="footer-brand">
              <div className="brand-icon-wrapper small">
                <ShieldCheck size={18} className="brand-icon" />
              </div>
              <span className="brand-name">
                Thrive <span className="brand-highlight">Treasury AI</span>
              </span>
            </div>
            <p className="footer-tagline">
              AI-powered financial reconciliation and exception intelligence platform.
            </p>
            <div className="buildathon-badge">
              Built for the <strong>Razorpay AI Buildathon</strong>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="footer-links-group">
            <div className="footer-links-col">
              <span className="footer-col-title">Navigation</span>
              <ul className="footer-links-list">
                <li><a href="#hero">Overview</a></li>
                <li><a href="#architecture">Architecture</a></li>
                <li><a href="#why-thrive">Principles</a></li>
              </ul>
            </div>

            <div className="footer-links-col">
              <span className="footer-col-title">Capabilities</span>
              <ul className="footer-links-list">
                <li><span>Deterministic Matching</span></li>
                <li><span>AI Exception Investigation</span></li>
                <li><span>Human-in-the-Loop Review</span></li>
                <li><span>Structured Action Log</span></li>
              </ul>
            </div>

            <div className="footer-links-col">
              <span className="footer-col-title">Access</span>
              <ul className="footer-links-list">
                <li><a href="/app" className="footer-cta-link">Get Started</a></li>
              </ul>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <p className="footer-copyright">
            © {currentYear} Thrive Treasury AI. Developed for the Razorpay AI Buildathon.
          </p>
          <p className="footer-notice">
            Designed for transparent reconciliation without simulated metrics or unverified performance claims.
          </p>
        </div>
      </div>
    </footer>
  )
}
