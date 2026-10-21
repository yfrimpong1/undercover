import { listClaims, type ClaimSummary } from "./api";
import { DecisionBadge, StatusBadge, Unreachable } from "./Badges";
import { date, label, money, STATUSES } from "./format";
import { usePolling } from "./usePolling";

function Payout({ claim }: Readonly<{ claim: ClaimSummary }>) {
  if (claim.payout === null || claim.decision !== "approve") return null;
  return (
    <>
      <span className="mono">{money(claim.payout)}</span>
      <span className="note">{claim.paid ? "Paid" : "Not paid"}</span>
    </>
  );
}

export function QueuePage() {
  const { data: claims, error } = usePolling(listClaims);
  if (error) return <Unreachable />;
  if (!claims) return <p className="note">Loading the queue…</p>;

  return (
    <>
      <h1>Claims queue</h1>
      <ul className="counts" aria-label="Claims by status">
        {STATUSES.map((status) => (
          <li className="panel count" key={status}>
            <span className="count-number" data-testid={`count-${status}`}>
              {claims.filter((claim) => claim.status === status).length}
            </span>
            <StatusBadge status={status} />
          </li>
        ))}
      </ul>
      <section className="panel table-panel">
        <table className="queue">
          <thead>
            <tr>
              <th scope="col">Claim</th>
              <th scope="col">Customer</th>
              <th scope="col">Type</th>
              <th scope="col">Submitted</th>
              <th scope="col" className="amount">
                Claimed
              </th>
              <th scope="col">Status</th>
              <th scope="col">Decision</th>
              <th scope="col" className="amount">
                Payout
              </th>
            </tr>
          </thead>
          <tbody>
            {claims.map((claim) => (
              <tr key={claim.claim_id} data-testid={`row-${claim.claim_id}`}>
                <td className="nowrap">
                  <a className="mono" href={`/claims/${claim.claim_id}`}>
                    {claim.claim_id}
                  </a>
                </td>
                <td>{claim.customer_name}</td>
                <td>
                  {label(claim.claim_type)}
                  <span className="note">{claim.summary}</span>
                </td>
                <td className="nowrap">{date(claim.submitted_on)}</td>
                <td className="amount mono">{money(claim.amount_claimed)}</td>
                <td>
                  <StatusBadge status={claim.status} />
                </td>
                <td>
                  {claim.decision && (
                    <DecisionBadge decision={claim.decision} />
                  )}
                </td>
                <td className="amount">
                  <Payout claim={claim} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
