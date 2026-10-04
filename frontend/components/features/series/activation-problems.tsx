import type { ActivationProblem } from "@/hooks/use-content-series";

const languageNames: Record<string, string> = { en: "English", ur: "Urdu" };

/** Group every backend activation problem by step and language. */
export function ActivationProblems({
  problems,
}: {
  problems: ActivationProblem[];
}): React.JSX.Element | null {
  if (!problems.length) return null;
  const groups = Map.groupBy(problems, (problem) => {
    const step = problem.step === null ? "Series" : `Step ${problem.step}`;
    const language = problem.language
      ? ` · ${languageNames[problem.language] ?? problem.language}`
      : "";
    return `${step}${language}`;
  });
  return (
    <section
      className="border-danger/30 bg-danger/5 rounded-card mt-4 border p-4 text-left"
      role="alert"
    >
      <h2 className="text-danger font-semibold">Series needs attention</h2>
      <p className="text-muted-foreground mt-1 text-sm">
        Fix these problems before activating the series.
      </p>
      <div className="mt-3 space-y-3">
        {Array.from(groups.entries()).map(([group, items]) => (
          <div key={group}>
            <h3 className="text-sm font-semibold">{group}</h3>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">
              {items.map((problem, index) => (
                <li key={`${problem.field}-${index}`}>
                  <span className="capitalize">
                    {problem.field.replaceAll("_", " ")}
                  </span>
                  : {problem.reason}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
