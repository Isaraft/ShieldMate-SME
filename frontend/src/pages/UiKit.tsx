import { T, tr } from '../i18n';
import { useRef, useState } from 'react';
import {
  Alert,
  Badge,
  Button,
  Field,
  LoadingState,
} from '../components/ui/Primitives';
import { Table } from '../components/ui/Table';
const statuses = [
  {
    label: 'Information',
    tone: 'neutral',
    meaning: 'Context and availability',
  },
  { label: 'Success', tone: 'success', meaning: 'An operation completed' },
  { label: 'Warning', tone: 'warning', meaning: 'Attention or a limitation' },
  { label: 'Error', tone: 'error', meaning: 'An operation failed' },
] as const;
export function UiKit() {
  const [value, setValue] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const form = useRef<HTMLFormElement>(null);
  return (
    <section className="workspace-page ui-kit">
      <p className="eyebrow">
        <T text={'Design system / Interactive reference'} />
      </p>
      <h1>
        <T text={'UI foundation'} />
      </h1>
      <p className="prose">
        <T
          text={
            'A working reference for the interface’s shared controls. These examples run locally in this page; nothing is saved or sent.'
          }
        />
      </p>
      <div className="kit-grid">
        <section className="kit-section">
          <h2>
            <T text={'Actions & feedback'} />
          </h2>
          <p>
            <T
              text={
                'Try the field to inspect validation, focus and success feedback. Use any non-sensitive example label.'
              }
            />
          </p>
          <form
            ref={form}
            noValidate
            onSubmit={(event) => {
              event.preventDefault();
              if (value.trim().length < 3) {
                setError('Enter at least 3 characters.');
                setSuccess(false);
                form.current?.querySelector('input')?.focus();
              } else {
                setError('');
                setSuccess(true);
              }
            }}
          >
            <Field
              label={tr('Example label')}
              help={tr('Component example only. 3–40 characters.')}
              maxLength={40}
              required
              value={value}
              error={tr(error)}
              onChange={(event) => {
                setValue(event.target.value);
                setError('');
                setSuccess(false);
              }}
            />
            <div className="button-row">
              <Button type="submit">
                <T text={'Try validation'} />
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setValue('');
                  setError('');
                  setSuccess(false);
                }}
              >
                <T text={'Reset'} />
              </Button>
            </div>
          </form>
          {success && (
            <Alert title={tr('Example validated')} tone="success">
              <p>
                <T
                  text={'The local input passed validation. Nothing was saved.'}
                />
              </p>
            </Alert>
          )}
          <div className="button-row">
            <Button disabled>
              <T text={'Unavailable'} />
            </Button>
            <Button variant="quiet" pending>
              <T text={'Pending'} />
            </Button>
          </div>
          <p className="field-help">
            <T
              text={'Disabled and pending states above are visual references.'}
            />
          </p>
        </section>
        <section className="kit-section">
          <h2>
            <T text={'Status has a name.'} />
          </h2>
          <p>
            <T
              text={
                'Color reinforces a written label. These are component examples, not security findings.'
              }
            />
          </p>
          <Table
            caption={tr('Semantic status reference')}
            columns={[
              {
                key: 'label',
                title: 'Status',
                render: (row: (typeof statuses)[number]) => (
                  <Badge tone={row.tone}>{tr(row.label)}</Badge>
                ),
              },
              {
                key: 'meaning',
                title: 'Use',
                render: (row) => tr(row.meaning),
              },
            ]}
            rows={[...statuses]}
            rowKey={(row) => row.label}
          />
          <LoadingState
            label={tr('Loading state example — no request in progress')}
          />
          <Alert title={tr('Permission pattern')} tone="warning">
            <p>
              <T
                text={
                  'Explain what permission is required and how to obtain it. No protected resources exist in this preview.'
                }
              />
            </p>
          </Alert>
        </section>
      </div>
    </section>
  );
}
