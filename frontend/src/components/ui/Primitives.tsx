import {
  useId,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
} from 'react';
type Tone = 'neutral' | 'success' | 'warning' | 'error';
export function Button({
  variant = 'primary',
  pending = false,
  children,
  className = '',
  disabled,
  type = 'button',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'quiet';
  pending?: boolean;
}) {
  return (
    <button
      {...props}
      type={type}
      disabled={disabled || pending}
      aria-busy={pending || undefined}
      className={`button button-${variant} ${className}`}
    >
      {pending ? 'Please wait…' : children}
    </button>
  );
}
export function Badge({
  children,
  tone = 'neutral',
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
export function Alert({
  children,
  title,
  tone = 'neutral',
}: {
  children: ReactNode;
  title: string;
  tone?: Tone;
}) {
  return (
    <div
      className={`feedback feedback-${tone}`}
      role={tone === 'error' ? 'alert' : 'status'}
    >
      <strong>{title}</strong>
      <div>{children}</div>
    </div>
  );
}
export function Field({
  label,
  help,
  error,
  id,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  help: string;
  error?: string;
}) {
  const generatedId = useId();
  const fieldId = id ?? generatedId;
  return (
    <div className="field">
      <label htmlFor={fieldId}>{label}</label>
      <input
        {...props}
        id={fieldId}
        aria-invalid={Boolean(error)}
        aria-describedby={`${fieldId}-help${error ? ` ${fieldId}-error` : ''}`}
      />
      <p id={`${fieldId}-help`} className="field-help">
        {help}
      </p>
      {error && (
        <p id={`${fieldId}-error`} className="field-error" role="alert">
          Error: {error}
        </p>
      )}
    </div>
  );
}
export function EmptyState({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty-state">
      <span className="empty-symbol" aria-hidden="true">
        [ — ]
      </span>
      <h2>{title}</h2>
      <div className="prose">{children}</div>
    </div>
  );
}
export function LoadingState({ label }: { label: string }) {
  return (
    <div className="loading-state" role="status">
      <span className="loading-line" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
