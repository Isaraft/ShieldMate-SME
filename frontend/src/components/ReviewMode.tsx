export function ReviewMode({
  technical,
  setTechnical,
}: {
  technical: boolean;
  setTechnical: (value: boolean) => void;
}) {
  return (
    <fieldset className="review-mode">
      <legend>Reading mode — same evidence and permissions</legend>
      <label>
        <input
          type="radio"
          name="reading-mode"
          checked={!technical}
          onChange={() => setTechnical(false)}
        />{' '}
        Business
      </label>
      <label>
        <input
          type="radio"
          name="reading-mode"
          checked={technical}
          onChange={() => setTechnical(true)}
        />{' '}
        Technical
      </label>
    </fieldset>
  );
}
