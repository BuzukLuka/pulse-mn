import { DOCS } from "./content";

export default function LegalIndex() {
  return (
    <div className="legal">
      <div className="eyebrow">Эрх зүй</div>
      <h1>Хууль эрх зүйн баримт бичиг</h1>
      <p className="muted">Pulse.mn-ийн хэрэглэгч бүрийн эрх, үүрэг. Persona бүрт хамаарах шаардлагыг тусад нь гаргасан.</p>
      <div className="grid" style={{ marginTop: 20 }}>
        {DOCS.map((d) => (
          <a key={d.slug} href={`/legal/${d.slug}`} className="card">
            <span className="badge blue">{d.audience}</span>
            <h3 style={{ marginTop: 10 }}>{d.title}</h3>
            <p className="muted" style={{ margin: 0 }}>{d.summary}</p>
          </a>
        ))}
      </div>
      <p className="muted" style={{ marginTop: 24 }}>⚖️ Эдгээр баримт нь платформын дотоод журам бөгөөд хуулийн зөвлөгөө биш. Хэрэгжүүлэхээс өмнө хуульчаар хянуулна уу.</p>
    </div>
  );
}
