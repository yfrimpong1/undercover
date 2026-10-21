import { useState, type SubmitEvent } from "react";
import { signOffClaim, type Claim, type Handler } from "./api";
import { DecisionBadge } from "./Badges";
import { dayOf, money } from "./format";

function PaymentLine({ claim }: Readonly<{ claim: Claim }>) {
  const { payment, sign_off: signOff } = claim;
  if (payment && signOff) {
    return (
      <p className="payment">
        Paid {money(payment.amount)}, signed off by {signOff.handler_name} on{" "}
        {dayOf(signOff.signed_off_at)}
      </p>
    );
  }
  if (payment) {
    return (
      <p className="payment">
        Paid {money(payment.amount)} on {dayOf(payment.paid_at)}
      </p>
    );
  }
  if (claim.status === "waiting_for_sign_off") {
    return <p className="payment">Waiting for a handler&apos;s sign-off</p>;
  }
  if (claim.decision?.decision === "approve") {
    return <p className="payment">Not paid yet</p>;
  }
  return <p className="payment">No payment</p>;
}

interface SignOffProps {
  claimId: string;
  payout: number;
  handlers: Handler[];
  onSignedOff: () => void;
}

function SignOffForm({
  claimId,
  payout,
  handlers,
  onSignedOff,
}: Readonly<SignOffProps>) {
  const eligible = handlers.filter((handler) => handler.can_approve_over_limit);
  const [handlerId, setHandlerId] = useState(eligible.at(0)?.handler_id ?? "");
  const [error, setError] = useState<string>();
  const [busy, setBusy] = useState(false);

  const submit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    signOffClaim(claimId, handlerId)
      .then(
        () => {
          setError(undefined);
          onSignedOff();
        },
        (reason: unknown) => {
          setError(reason instanceof Error ? reason.message : String(reason));
        },
      )
      .finally(() => {
        setBusy(false);
      });
  };

  return (
    <form className="sign-off" onSubmit={submit}>
      <label htmlFor="handler">Handler</label>
      <select
        id="handler"
        value={handlerId}
        onChange={(event) => {
          setHandlerId(event.target.value);
        }}
      >
        {eligible.map((handler) => (
          <option key={handler.handler_id} value={handler.handler_id}>
            {handler.name}
          </option>
        ))}
      </select>
      <button type="submit" disabled={busy}>
        Sign off and pay {money(payout)}
      </button>
      {error && (
        <p className="panel alert" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}

interface DecisionPanelProps {
  claim: Claim;
  handlers: Handler[];
  onSignedOff: () => void;
}

export function DecisionPanel({
  claim,
  handlers,
  onSignedOff,
}: Readonly<DecisionPanelProps>) {
  const { decision } = claim;
  return (
    <section className="panel" aria-labelledby="decision-heading">
      <h2 id="decision-heading">The agent&apos;s decision</h2>
      {decision ? (
        <>
          <p className="decision-line">
            <DecisionBadge decision={decision.decision} />
            <span className="payout">{money(decision.payout)}</span>
          </p>
          <p className="reason">{decision.reason}</p>
          <p className="note">Policy section</p>
          <details className="wording-section">
            <summary>{decision.policy_section_title}</summary>
            <div className="wording">{decision.policy_section_text}</div>
          </details>
          <PaymentLine claim={claim} />
          {claim.status === "waiting_for_sign_off" && (
            <SignOffForm
              claimId={claim.claim_id}
              payout={decision.payout}
              handlers={handlers}
              onSignedOff={onSignedOff}
            />
          )}
        </>
      ) : (
        <p className="note">The agent hasn&apos;t decided this claim yet.</p>
      )}
    </section>
  );
}
