import { T } from '../i18n';
export function ReviewMode({
  technical,
  setTechnical,
}: {
  technical: boolean;
  setTechnical: (value: boolean) => void;
}) {
  return (
    <fieldset className="review-mode">
      <legend>
        <T text={'Reading mode — same evidence and permissions'} />
      </legend>
      <label>
        <input
          type="radio"
          name="reading-mode"
          checked={!technical}
          onChange={() => setTechnical(false)}
        />{' '}
        <T text={'Business'} />
      </label>
      <label>
        <input
          type="radio"
          name="reading-mode"
          checked={technical}
          onChange={() => setTechnical(true)}
        />{' '}
        <T text={'Technical'} />
      </label>
    </fieldset>
  );
}
