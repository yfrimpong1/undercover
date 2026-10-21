import { getInstructions } from "./api";
import { Unreachable } from "./Badges";
import { usePolling } from "./usePolling";

export function InstructionsPage() {
  const { data, error } = usePolling(getInstructions);
  if (error) return <Unreachable />;
  if (!data) return <p className="note">Loading the instructions…</p>;

  return (
    <>
      <h1>Agent instructions</h1>
      <p className="lede">
        What the UnderCover Agent is told at the start of every claim. They are
        read only.
      </p>
      <pre className="panel instructions">{data.text}</pre>
    </>
  );
}
