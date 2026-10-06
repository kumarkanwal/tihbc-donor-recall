import {
  expect,
  test as base,
  type Page,
  type TestInfo,
} from "@playwright/test";

function safeUrl(value: string): string {
  try {
    const url = new URL(value);
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch {
    return "<unparseable URL>";
  }
}

function observeBrowser(page: Page, diagnostics: string[]): void {
  page.on("console", (message) => {
    if (message.type() !== "error") return;
    const location = message.location();
    const source = location.url
      ? ` (${safeUrl(location.url)}:${location.lineNumber})`
      : "";
    diagnostics.push(`[console.error] ${message.text()}${source}`);
  });
  page.on("pageerror", (error) => {
    diagnostics.push(`[pageerror] ${error.stack ?? error.message}`);
  });
  page.on("requestfailed", (request) => {
    const reason = request.failure()?.errorText ?? "unknown failure";
    diagnostics.push(
      `[requestfailed] ${request.method()} ${safeUrl(request.url())}: ${reason}`,
    );
  });
  page.on("response", (response) => {
    if (response.status() < 400) return;
    diagnostics.push(
      `[http ${response.status()}] ${response.request().method()} ${safeUrl(response.url())}`,
    );
  });
}

async function reportFailure(
  diagnostics: string[],
  testInfo: TestInfo,
): Promise<void> {
  if (testInfo.status === testInfo.expectedStatus) return;
  const details = diagnostics.length
    ? diagnostics.join("\n")
    : "No browser console errors or failed requests were captured.";
  const report = `Browser diagnostics for failed test "${testInfo.title}":\n${details}\n`;
  await testInfo.attach("browser-diagnostics", {
    body: Buffer.from(report),
    contentType: "text/plain",
  });
  process.stderr.write(`\n${report}`);
}

export const test = base.extend<{ browserDiagnostics: void }>({
  browserDiagnostics: [
    async ({ page }, use, testInfo) => {
      const diagnostics: string[] = [];
      observeBrowser(page, diagnostics);
      await use();
      await reportFailure(diagnostics, testInfo);
    },
    { auto: true },
  ],
});

export { expect };
