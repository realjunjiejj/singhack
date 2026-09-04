export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="empty-state" role="status">
      <span className="empty-mark" aria-hidden="true">○</span>
      <h2>{title}</h2>
      <p>{body}</p>
    </div>
  );
}
