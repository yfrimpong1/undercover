import { useCallback } from "react";
import {
  ApiError,
  getClaim,
  getCustomer,
  getPolicy,
  listHandlers,
  listSteps,
  type Claim,
  type Customer,
  type Policy,
} from "./api";
import { StatusBadge, Unreachable } from "./Badges";
import { DecisionPanel } from "./DecisionPanel";
import { date, label, money } from "./format";
import { StepsPanel } from "./StepsPanel";
import { usePolling } from "./usePolling";

async function loadClaimView(claimId: string) {
  const [claim, steps, handlers] = await Promise.all([
    getClaim(claimId),
    listSteps(claimId),
    listHandlers(),
  ]);
  const [policy, customer] = await Promise.all([
    getPolicy(claim.policy_id),
    getCustomer(claim.customer_id),
  ]);
  return { claim, steps, handlers, policy, customer };
}

function ClaimDetails({ claim }: Readonly<{ claim: Claim }>) {
  return (
    <section className="panel" aria-labelledby="claim-heading">
      <h2 id="claim-heading">The claim</h2>
      <dl className="facts">
        <dt>Incident</dt>
        <dd>
          {date(claim.incident_date)}, {claim.incident_location}
        </dd>
        <dt>Submitted</dt>
        <dd>{date(claim.submitted_on)}</dd>
      </dl>
      <h3>The customer&apos;s story</h3>
      <blockquote className="story">{claim.story}</blockquote>
      <h3>Items claimed</h3>
      <table className="items">
        <tbody>
          {claim.items.map((item) => (
            <tr key={item.description}>
              <td>{item.description}</td>
              <td className="note-cell">{label(item.category)}</td>
              <td className="amount mono">{money(item.amount)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr>
            <th scope="row" colSpan={2}>
              Amount claimed
            </th>
            <td className="amount mono">{money(claim.amount_claimed)}</td>
          </tr>
        </tfoot>
      </table>
      <h3>Documents</h3>
      <ul className="documents">
        {claim.documents.map((document) => (
          <li key={document.name} className="document">
            <p className="document-name">
              {document.name}
              <span className="note">{label(document.type)}</span>
            </p>
            <p>{document.content}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}

function PolicyPanel({ policy }: Readonly<{ policy: Policy }>) {
  const { plan, trip } = policy;
  return (
    <section className="panel" aria-labelledby="policy-heading">
      <h2 id="policy-heading">
        Policy <span className="mono">{policy.policy_id}</span>
      </h2>
      <dl className="facts">
        <dt>Plan</dt>
        <dd>{plan.name}</dd>
        <dt>Add-ons</dt>
        <dd>
          {policy.add_ons.map((addOn) => addOn.name).join(", ") || "None"}
        </dd>
        <dt>Bought</dt>
        <dd>
          {date(policy.purchased_on)}, through {policy.sold_through}
        </dd>
        <dt>Trip</dt>
        <dd>
          {trip.destination}, {date(trip.departs_on)} to {date(trip.returns_on)}
        </dd>
        <dt>Trip cost</dt>
        <dd className="mono">{money(trip.trip_cost)}</dd>
        <dt>Travelers</dt>
        <dd>{policy.travelers.join(", ")}</dd>
      </dl>
      <h3>Plan limits</h3>
      <dl className="facts limits">
        <dt>Trip cancellation</dt>
        <dd>{money(plan.trip_cancellation_max)}</dd>
        <dt>Trip delay</dt>
        <dd>
          {money(plan.trip_delay_max)} after {plan.trip_delay_waiting_hours}{" "}
          hours
        </dd>
        <dt>Baggage delay</dt>
        <dd>
          {money(plan.baggage_delay_max)} after{" "}
          {plan.baggage_delay_waiting_hours} hours
        </dd>
        <dt>Baggage</dt>
        <dd>
          {money(plan.baggage_max)}, {money(plan.per_item_limit)} an item
        </dd>
        <dt>Passport</dt>
        <dd>{money(plan.passport_max)}</dd>
        <dt>Emergency medical</dt>
        <dd>{money(plan.emergency_medical_max)}</dd>
        <dt>Deductible</dt>
        <dd>{money(plan.deductible)}</dd>
      </dl>
    </section>
  );
}

function CustomerPanel({ customer }: Readonly<{ customer: Customer }>) {
  const { address } = customer;
  return (
    <section className="panel" aria-labelledby="customer-heading">
      <h2 id="customer-heading">Customer</h2>
      <dl className="facts">
        <dt>Name</dt>
        <dd>{customer.name}</dd>
        <dt>Email</dt>
        <dd>{customer.email}</dd>
        <dt>Phone</dt>
        <dd>{customer.phone}</dd>
        <dt>Address</dt>
        <dd>
          {address.street}, {address.city}, {address.state} {address.zip}
        </dd>
        <dt>Customer since</dt>
        <dd>{date(customer.customer_since)}</dd>
      </dl>
      <h3>Earlier claims</h3>
      {customer.previous_claims.length === 0 ? (
        <p className="note">None</p>
      ) : (
        <ul className="history">
          {customer.previous_claims.map((previous) => (
            <li key={previous.claim_id}>
              <span className="mono">{previous.claim_id}</span>,{" "}
              {date(previous.filed_on)}, {label(previous.claim_type)}
              <span className="note">
                {previous.summary}. {label(previous.outcome)},{" "}
                {money(previous.amount_paid)} paid.
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function ClaimPage({ claimId }: Readonly<{ claimId: string }>) {
  const load = useCallback(() => loadClaimView(claimId), [claimId]);
  const { data, error, refresh } = usePolling(load);
  if (error instanceof ApiError && error.status === 404) {
    return <p className="panel">Claim {claimId} not found.</p>;
  }
  if (error) return <Unreachable />;
  if (!data) return <p className="note">Loading the claim…</p>;

  const { claim, steps, handlers, policy, customer } = data;
  return (
    <>
      <p>
        <a href="/">Claims queue</a>
      </p>
      <div className="claim-title">
        <h1>
          <span className="mono">{claim.claim_id}</span> {claim.summary}
        </h1>
        <StatusBadge status={claim.status} />
      </div>
      <p className="lede">
        {label(claim.claim_type)} claim from {claim.customer_name} for{" "}
        {money(claim.amount_claimed)}
      </p>
      <div className="claim-layout">
        <div>
          <DecisionPanel
            claim={claim}
            handlers={handlers}
            onSignedOff={refresh}
          />
          <ClaimDetails claim={claim} />
          <StepsPanel steps={steps} />
        </div>
        <div>
          <PolicyPanel policy={policy} />
          <CustomerPanel customer={customer} />
        </div>
      </div>
    </>
  );
}
