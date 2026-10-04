import Image from "next/image";

/** Authentication route placeholder completed in Task 3.3. */
export default function LoginPage(): React.JSX.Element {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <section className="rounded-card border-border bg-surface shadow-surface w-full max-w-md border p-8 text-center">
        <span className="mx-auto block w-fit rounded-lg bg-white p-1.5">
          <Image
            src="/images/IHHN-Logo-02-150x150.webp"
            alt="Indus Hospital and Health Network"
            width={96}
            height={96}
            priority
          />
        </span>
        <h1 className="mt-6 text-2xl font-semibold">Donor Recall</h1>
        <p className="text-muted-foreground mt-2">
          Sign-in setup is coming next.
        </p>
      </section>
    </main>
  );
}
