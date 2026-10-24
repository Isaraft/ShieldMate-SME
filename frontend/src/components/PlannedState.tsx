import { T } from '../i18n';
type PlannedStateProps = {
  title: string;
  phase: string;
  children: React.ReactNode;
};

export function PlannedState({ title, phase, children }: PlannedStateProps) {
  return (
    <section className="planned-state" aria-labelledby="page-title">
      <p className="eyebrow">
        <T text={'Planned · '} />
        {phase}
      </p>
      <h1 id="page-title">{title}</h1>
      <p className="availability">
        <T text={'Coming in a later phase'} />
      </p>
      <div className="prose">{children}</div>
      <p className="empty-note">
        <T text={'No workspace data is collected or stored in this preview.'} />
      </p>
    </section>
  );
}
