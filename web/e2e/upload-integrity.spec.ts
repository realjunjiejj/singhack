import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";

test("adopting a new dataset clears approval and replaces the executive story", async ({ page }) => {
  const workbench = JSON.parse(readFileSync(path.resolve(process.cwd(), "../artifacts/workbench.json"), "utf8"));
  const clientCase = workbench.clientCases.find((item: { clientId: string }) => item.clientId === "CL-0001");
  clientCase.meetingBrief.whatChanged = "Uploaded evidence: review the updated funding plan.";
  await page.route("**/api/analysis/health", (route) => route.fulfill({ json: { status: "ready", geminiConfigured: false } }));
  await page.route("**/api/analysis", (route) => route.fulfill({ json: {
    schemaVersion: "1.0.0", runId: "replacement", generatedAt: workbench.meta.generatedAt,
    status: "completed", deepFocus: [], diagnostics: [], agentReports: [], workbench,
  } }));
  await page.goto("/");
  await page.getByRole("button", { name: "Hartono", exact: true }).click();
  await page.getByRole("button", { name: /prepare conversation/i, exact: true }).click();
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(page.getByText("Approved revision 1")).toBeVisible();
  await page.getByRole("button", { name: "Close work surface" }).click();
  await page.getByRole("button", { name: "Upload & analyse", exact: true }).click();
  await page.locator('input[type="file"]').setInputFiles({ name: "clients.csv", mimeType: "text/csv", buffer: Buffer.from("mock transport; engine response is intercepted") });
  await page.getByRole("button", { name: "Upload & analyse automatically" }).click();
  await expect(page.getByRole("dialog")).not.toBeAttached();
  await page.getByRole("button", { name: "Hartono", exact: true }).click();
  await expect(page.locator(".ai-executive-analysis").getByText(clientCase.meetingBrief.whatChanged)).toBeVisible();
  await page.getByRole("button", { name: /prepare conversation/i, exact: true }).click();
  await expect(page.getByText("Draft · revision 1")).toBeVisible();
  await expect(page.getByRole("button", { name: "Mark conversation prepared" })).toBeDisabled();
});
