import { InstructionsPage } from "./InstructionsPage";
import { QueuePage } from "./QueuePage";

function Page({ path }: Readonly<{ path: string }>) {
  if (path === "/instructions") return <InstructionsPage />;
  return <QueuePage />;
}

export function App({ path }: Readonly<{ path: string }>) {
  const current = (href: string) => (path === href ? "page" : undefined);
  return (
    <>
      <header className="site-header">
        <a className="brand" href="/">
          UnderCover <span className="tagline">Claims</span>
        </a>
        <nav aria-label="Main">
          <a href="/" aria-current={current("/")}>
            Claims
          </a>
          <a href="/instructions" aria-current={current("/instructions")}>
            Agent instructions
          </a>
        </nav>
      </header>
      <main>
        <Page path={path} />
      </main>
    </>
  );
}
