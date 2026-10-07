export default function Recommendations({ items }) {
  if (!items?.length) return null;
  return (
    <ul className="recs">
      {items.map((r, i) => (
        <li key={`${r.reason}-${i}`} className={`rec p${r.priority}`}>
          <h3>{r.title}</h3>
          <p>{r.detail}</p>
        </li>
      ))}
    </ul>
  );
}
