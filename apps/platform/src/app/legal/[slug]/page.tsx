import { notFound } from "next/navigation";
import { DOCS } from "../content";

export function generateStaticParams() {
  return DOCS.map((d) => ({ slug: d.slug }));
}

export default function LegalDoc({ params }: { params: { slug: string } }) {
  const d = DOCS.find((x) => x.slug === params.slug);
  if (!d) notFound();
  return (
    <article className="legal">
      <nav className="crumbs"><a href="/legal">Эрх зүй</a><span>/</span><span className="badge blue">{d.audience}</span></nav>
      <h1 style={{ marginTop: 12 }}>{d.title}</h1>
      <p className="muted">{d.summary}</p>
      {d.sections.map((s) => (
        <section key={s.h}><h2>{s.h}</h2><ul>{s.items.map((i) => <li key={i}>{i}</li>)}</ul></section>
      ))}
      <div className="card" style={{ marginTop: 24 }}>
        <h3>Холбогдох хууль тогтоомж</h3>
        <ul className="law">{d.laws.map((l) => <li key={l}>{l}</li>)}</ul>
        <p className="muted" style={{ marginBottom: 0 }}>⚖️ Платформын дотоод журам — хуулийн зөвлөгөө биш. Хууль тогтоомж өөрчлөгдвөл шинэчилнэ.</p>
      </div>
    </article>
  );
}
