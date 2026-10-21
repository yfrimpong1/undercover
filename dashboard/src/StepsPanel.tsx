import type { Step } from "./api";
import { time } from "./format";

function pretty(content: string): string {
  try {
    return JSON.stringify(JSON.parse(content), null, 2);
  } catch {
    return content;
  }
}

function StepBody({ step }: Readonly<{ step: Step }>) {
  const at = <span className="step-time">{time(step.created_at)}</span>;
  if (step.kind === "message") {
    return (
      <>
        <p className="step-label">The agent says {at}</p>
        <p className="step-text">{step.content}</p>
      </>
    );
  }
  if (step.kind === "tool_call") {
    return (
      <>
        <p className="step-label">
          Calls <code>{step.name}</code> {at}
        </p>
        {step.content !== "{}" && <code className="args">{step.content}</code>}
      </>
    );
  }
  return (
    <details>
      <summary className="step-label">
        Result of <code>{step.name}</code> {at}
      </summary>
      <pre className="result">{pretty(step.content)}</pre>
    </details>
  );
}

export function StepsPanel({ steps }: Readonly<{ steps: Step[] }>) {
  return (
    <section className="panel" aria-labelledby="steps-heading">
      <h2 id="steps-heading">The agent&apos;s steps</h2>
      {steps.length === 0 ? (
        <p className="note">The agent hasn&apos;t started on this claim.</p>
      ) : (
        <ol className="steps">
          {steps.map((step) => (
            <li key={step.step_id} className={`step step-${step.kind}`}>
              <StepBody step={step} />
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
