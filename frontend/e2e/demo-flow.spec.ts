import { expect, test, type Page } from "@playwright/test";
import path from "node:path";

const ADMIN = {
  email: "admin@tihbc.demo",
  password: "ChangeMe123!",
} as const;
const COORDINATOR = {
  email: "coordinator@tihbc.demo",
  password: "ChangeMe123!",
} as const;
const SAMPLE_FILE = path.resolve(
  process.cwd(),
  "../backend/app/seed/assets/sample-donors.xlsx",
);

async function loginAsAdmin(page: Page): Promise<void> {
  await login(page, ADMIN.email, ADMIN.password);
}

async function uploadSampleFile(page: Page, batchName: string): Promise<void> {
  await page.getByTestId("nav-batches").click();
  await page.getByTestId("upload-batch-action").click();
  await page.getByTestId("batch-name-input").fill(batchName);
  await page.getByTestId("batch-file-input").setInputFiles(SAMPLE_FILE);
  await page.getByTestId("batch-review-submit").click();
  await expect(page.getByTestId("batch-review-step")).toBeVisible();
  await expect(page.getByTestId("batch-review-valid-rows")).toHaveAttribute(
    "data-value",
    "35",
  );
}

async function importReviewedBatch(page: Page): Promise<void> {
  await page.getByTestId("batch-review-continue").click();
  await expect(page.getByTestId("batch-confirm-step")).toBeVisible();
  await page.getByTestId("batch-import-trigger").click();
  await page.getByTestId("confirm-dialog-submit").click();
  await expect(page.getByTestId("batch-import-success")).toBeVisible();
}

async function createAndLaunchCampaign(
  page: Page,
  batchName: string,
  campaignName: string,
): Promise<void> {
  await page.getByTestId("batch-create-campaign-action").click();
  await page.getByTestId("campaign-name-input").fill(campaignName);
  await page
    .getByTestId("campaign-batch-select")
    .selectOption({ label: `${batchName} · 35 donors` });
  await page
    .getByTestId("campaign-primary-series-select")
    .selectOption({ label: "First-Time Donor Return" });
  await page
    .getByTestId("campaign-secondary-series-select")
    .selectOption({ label: "Final Follow-up" });
  await page.getByTestId("campaign-launch-trigger").click();
  await page.getByTestId("confirm-dialog-submit").click();
  await expect(page.getByTestId("campaign-detail")).toBeVisible();
  await expect(page).toHaveURL(/\/campaigns\/[0-9a-f-]+$/);
}

async function skipTime(page: Page): Promise<void> {
  await page.getByTestId("skip-time-trigger").click();
  await page.getByTestId("skip-time-0-days-1-hours").click();
  await expect(
    page.getByText("Demo time updated", { exact: true }),
  ).toBeVisible();
}

async function confirmFromDonorPhone(
  page: Page,
  campaignName: string,
): Promise<string> {
  await page.getByTestId("donor-phone-launcher").click();
  await expect(page.getByTestId("donor-phone-panel")).toBeVisible();
  await page
    .getByTestId("simulator-campaign-filter")
    .selectOption({ label: campaignName });
  const donor = page.getByTestId("simulator-conversation-row").first();
  await expect(donor).toBeVisible();
  const donorName = await donor.getAttribute("data-donor-name");
  expect(donorName).toBeTruthy();
  await donor.click();
  const messages = page.getByTestId("simulator-message");
  const messageCount = await messages.count();
  await page.getByTestId("simulator-reply-btn_confirm").last().click();
  await expect(messages).toHaveCount(messageCount + 2);
  await expect(messages.last()).toContainText(/Thank you,|شکریہ/);
  return donorName ?? "";
}

async function verifyCampaignCounterUpdated(page: Page): Promise<void> {
  await page.getByTestId("donor-phone-close").click();
  await expect(
    page.getByTestId("enrollment-status-confirmed"),
  ).not.toHaveAttribute("data-count", "0");
}

async function verifyFollowUpInInbox(
  page: Page,
  donorName: string,
): Promise<void> {
  await page.getByTestId("nav-inbox").click();
  await page.getByTestId("inbox-tab-confirmed").click();
  await page.getByTestId("inbox-search").fill(donorName);
  await expect(
    page.getByTestId("follow-up-item").filter({ hasText: donorName }),
  ).toBeVisible();
}

async function verifyDashboardKpis(page: Page): Promise<void> {
  await page.getByTestId("nav-dashboard").click();
  for (const testId of [
    "dashboard-kpi-donors-reached",
    "dashboard-kpi-delivery-rate",
    "dashboard-kpi-response-rate",
    "dashboard-kpi-confirmed",
  ]) {
    await expect.poll(async () => metricValue(page, testId)).toBeGreaterThan(0);
  }
}

async function logout(page: Page): Promise<void> {
  await page.getByTestId("user-menu-trigger").click();
  await page.getByTestId("logout-action").click();
  await expect(page.getByTestId("login-submit")).toBeVisible();
}

async function loginAsCoordinatorAndVerifyAdminControlsHidden(
  page: Page,
): Promise<void> {
  await login(page, COORDINATOR.email, COORDINATOR.password);
  await expect(page.getByTestId("skip-time-trigger")).toHaveCount(0);

  await page.getByTestId("nav-batches").click();
  await expect(page.getByTestId("upload-batch-action")).toHaveCount(0);

  await page.getByTestId("nav-campaigns").click();
  await expect(page.getByTestId("new-campaign-action")).toHaveCount(0);

  await page.getByTestId("nav-settings").click();
  await expect(page.getByTestId("settings-tab-demo")).toHaveCount(0);
}

async function login(
  page: Page,
  email: string,
  password: string,
): Promise<void> {
  await page.goto("/login");
  await page.getByTestId("login-email").fill(email);
  await page.getByTestId("login-password").fill(password);
  await page.getByTestId("login-submit").click();
  await expect(page.getByTestId("nav-dashboard")).toBeVisible();
}

async function metricValue(page: Page, testId: string): Promise<number> {
  const value = await page.getByTestId(testId).getAttribute("data-value");
  return Number.parseFloat((value ?? "0").replace(/[,%]/g, ""));
}

test.describe("TIHBC full demo story", () => {
  test("admin launches a recall and coordinator sees the result", async ({
    page,
  }) => {
    const suffix = Date.now();
    const batchName = `E2E donor batch ${suffix}`;
    const campaignName = `E2E recall campaign ${suffix}`;

    await loginAsAdmin(page);
    await uploadSampleFile(page, batchName);
    await importReviewedBatch(page);
    await createAndLaunchCampaign(page, batchName, campaignName);
    await skipTime(page);
    const donorName = await confirmFromDonorPhone(page, campaignName);
    await verifyCampaignCounterUpdated(page);
    await verifyFollowUpInInbox(page, donorName);
    await verifyDashboardKpis(page);
    await logout(page);
    await loginAsCoordinatorAndVerifyAdminControlsHidden(page);
  });
});
