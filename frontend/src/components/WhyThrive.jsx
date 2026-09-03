import { Binary, Cpu, UserCheck, LineChart } from 'lucide-react'

const PRINCIPLES = [
  {
    id: 'deterministic',
    number: '01',
    title: 'Deterministic Logic',
    principle: 'Deterministic logic where exact matching is possible.',
    detail: 'Clear records match instantly on mathematical identity without probabilistic LLM latency or cost.',
    icon: Binary,
  },
  {
    id: 'ai-reasoning',
    number: '02',
    title: 'AI Reasoning',
    principle: 'AI reasoning where ambiguity exists.',
    detail: 'Contextual AI investigates fee structures (MDR, GST) and unstructured notes to explain discrepancies.',
    icon: Cpu,
  },
  {
    id: 'human-review',
    number: '03',
    title: 'Human Review',
    principle: 'Human review when confidence is insufficient.',
    detail: 'Uncertain financial items are safely escalated to treasury specialists rather than blindly automated.',
    icon: UserCheck,
  },
  {
    id: 'measured-results',
    number: '04',
    title: 'Measured Results',
    principle: 'Measured results instead of unsupported claims.',
    detail: 'Every capability is backed by verifiable audit trails, honest demonstration data, and transparent logic.',
    icon: LineChart,
  },
]

export default function WhyThrive() {
  return (
    <section className="section-why-thrive" id="why-thrive">
      <div className="section-container">
        <div className="section-header">
          <div className="section-tag">Core Principles</div>
          <h2 className="section-title">Designed for Financial Truth</h2>
          <p className="section-description">
            Four foundational engineering principles that govern how Thrive Treasury AI handles money,
            discrepancies, and reconciliation decisions.
          </p>
        </div>

        <div className="concise-principles-row">
          {PRINCIPLES.map((item) => {
            const Icon = item.icon
            return (
              <div key={item.id} className="concise-principle-item">
                <div className="principle-item-header">
                  <span className="principle-item-num">{item.number}</span>
                  <div className="principle-item-icon">
                    <Icon size={18} />
                  </div>
                </div>
                <h3 className="principle-item-title">{item.title}</h3>
                <p className="principle-item-statement">"{item.principle}"</p>
                <p className="principle-item-detail">{item.detail}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
