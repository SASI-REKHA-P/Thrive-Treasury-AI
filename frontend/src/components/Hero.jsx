import { ArrowRight, Play, CheckCircle2, Cpu, UserCheck } from 'lucide-react'

export default function Hero() {
  const scrollToSimulation = () => {
    const el = document.getElementById('architecture') || document.getElementById('simulation') || document.getElementById('story')
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <section className="hero-section" id="hero">
      <div className="hero-container">
        {/* Main Hero Framing */}
        <div className="hero-content-center">
          <div className="hero-badge">
            <span className="badge-pill">Razorpay AI Buildathon</span>
            <span className="badge-text">Interactive Architectural Simulation</span>
          </div>

          <h1 className="hero-title">
            Reconcile Smarter. <br />
            Close Faster. <br />
            <span className="hero-title-highlight">Thrive.</span>
          </h1>

          <p className="hero-subtitle">
            An AI-powered reconciliation platform designed to compare payment and settlement records,
            detect discrepancies, investigate complex exceptions, and keep finance teams in control.
          </p>

          <div className="hero-cta-group">
            <a href="/app" className="btn-primary btn-large">
              <span>Get Started</span>
              <ArrowRight size={18} />
            </a>

            <button
              type="button"
              className="btn-secondary btn-large btn-watch-demo"
              onClick={scrollToSimulation}
            >
              <Play size={16} className="play-icon-fill" />
              <span>Watch Live Reconciliation</span>
            </button>
          </div>

          {/* Quick Engine Workflow Indicators */}
          <div className="hero-flow-preview">
            <div className="preview-node">
              <span className="node-dot green"></span>
              <CheckCircle2 size={15} className="node-icon green" />
              <span>Deterministic Matching</span>
            </div>
            <span className="node-arrow">→</span>
            <div className="preview-node">
              <span className="node-dot purple"></span>
              <Cpu size={15} className="node-icon purple" />
              <span>Contextual AI Investigation</span>
            </div>
            <span className="node-arrow">→</span>
            <div className="preview-node">
              <span className="node-dot amber"></span>
              <UserCheck size={15} className="node-icon amber" />
              <span>Human Review Queue</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
