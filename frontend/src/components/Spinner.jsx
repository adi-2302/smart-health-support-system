export function Spinner({ label = "Loading" }) {
  return <div className="spinner" role="status" aria-label={label} />;
}

export function ErrorBox({ error, onRetry }) {
  if (!error) return null;
  return (
    <div className="notice error" role="alert">
      {error}
      {onRetry && <> <button className="btn ghost small" style={{ marginLeft: 8 }} onClick={onRetry}>Retry</button></>}
    </div>
  );
}
