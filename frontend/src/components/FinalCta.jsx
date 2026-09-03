import { ArrowRight, ShieldCheck } from 'lucide-react'

export default function FinalCta() {
  return (
    <section className="section-final-cta">
      <div className="section-container">
        <div className="final-cta-card">
          <div className="cta-glow-bg"></div>

          <div className="cta-content">
            <div className="cta-badge">
              <ShieldCheck size={16} />
              <span>Thrive Treasury AI</span>
            </div>

            <h2 className="cta-headline">Ready to reconcile smarter?</h2>

            <p className="cta-subtext">
              Transform your payment and settlement reconciliation workflows with intelligent
              matching rules, AI-assisted exception analysis, and full human governance.
            </p>

            <div className="cta-actions">
              <a href="/app" className="btn-primary btn-large">
                <span>Get Started</span>
                <ArrowRight size={18} />
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
