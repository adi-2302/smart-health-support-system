export default function EarlyWarning({ warning }) {
  if (!warning?.triggered) return null;
  return (
    <div className="alert" role="alert">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /><path d="M12 9v4M12 17h.01" />
      </svg>
      <div>
        <strong>Early-warning check</strong>
        {warning.message} It might help to talk to someone you trust, or your college counselling service, before it builds up.
      </div>
    </div>
  );
}
