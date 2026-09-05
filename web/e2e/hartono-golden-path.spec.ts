import { expect, test } from "@playwright/test";

test("Hartono Queue to Evidence Chain to approved Meeting Brief", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await expect(page.getByText("Generated · attention")).toBeVisible();
  await expect(page.getByText("20/20")).toBeVisible();
  await page.getByRole("button", { name: /Hartono Wijaya Kusuma/ }).click();
  await expect(page.getByRole("heading", { name: "Hartono Wijaya Kusuma", exact: true })).toBeVisible();
  await expect(page.getByText("Historical — resolved").first()).toBeVisible();
  await expect(page.getByText("ACTUAL INTELLIGENCE · DEEP CLIENT ADVISORY")).toBeVisible();
  await expect(page.getByText("WHAT HAPPENED")).toBeVisible();
  await expect(page.getByText("THE CLIENT DILEMMA")).toBeVisible();
  await expect(page.getByText("WHAT SHOULD BE DONE")).toBeVisible();
  await expect(page.getByText("HOW TO OPEN THE CONVERSATION")).toBeVisible();
  await expect(page.getByRole("heading", { name: "AI-assisted insights for this client" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Portfolio allocation by asset class" })).toBeVisible();
  await page.screenshot({ path: "demo/screenshots/01-priority-queue.png", fullPage: true });

  await page.locator(".client-pulse").getByText(/Evidence · \d+ cited records/).first().click();
  await page.getByRole("button", { name: /Open evidence .*LTV_2025_12_31/ }).first().click();
  await expect(page.getByRole("heading", { name: "Evidence Chain" })).toBeVisible();
  await expect(page.getByText("credit_facilities.csv").first()).toBeVisible();
  await expect(page.getByText("78.5").first()).toBeVisible();
  await expect(page.getByText(/drawn amount \/ lending value/i)).toBeAttached();
  await page.screenshot({ path: "demo/screenshots/02-hartono-evidence.png", fullPage: true });

  await page.getByRole("button", { name: "Close work surface" }).click();
  await page.getByRole("button", { name: "Explore supplied collateral what-if" }).click();
  await page.getByLabel("Supplied scenario").selectOption({ label: "-15% collateral · near" });
  await expect(page.getByText("69.59%")).toBeVisible();
  await expect(page.getByLabel("Collateral Stress Test").getByText("SGD 8,000,000", { exact: true })).toBeVisible();
  await expect(page.getByText(/not a forecast/i).first()).toBeVisible();
  await page.getByRole("button", { name: "Close work surface" }).click();
  await page.getByRole("button", { name: /prepare conversation/i, exact: true }).click();
  await expect(page.getByText("Draft · revision 1")).toBeVisible();
  await page.getByRole("button", { name: "Edit", exact: true }).click();
  const opening = page.getByRole("textbox", { name: "Respectful opening question" });
  await opening.fill("Could we review the lending buffer and property timing together?");
  await page.getByRole("button", { name: "Finish editing" }).click();
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(page.getByText("Approved revision 1")).toBeVisible();
  await page.getByRole("button", { name: "Mark conversation prepared" }).click();
  await expect(page.getByText(/Current · conversation prepared/)).toBeVisible();
  await page.screenshot({ path: "demo/screenshots/03-approved-meeting-brief.png", fullPage: true });

  await page.getByRole("button", { name: "Edit", exact: true }).click();
  await opening.fill("What flexibility would feel right for the property plan now?");
  await expect(page.getByText("Edited draft · revision 2")).toBeVisible();
  await expect(page.getByText(/Current · unresolved/)).toBeVisible();
});

test("presentation widths have no horizontal page overflow", async ({ page }) => {
  for (const viewport of [{ width: 1440, height: 900 }, { width: 1280, height: 800 }, { width: 1000, height: 800 }]) {
    await page.setViewportSize(viewport);
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Priority Queue" })).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(0);
    if (viewport.width === 1280) await page.screenshot({ path: "demo/screenshots/04-responsive-1280.png", fullPage: true });
    if (viewport.width === 1000) {
      await page.getByRole("button", { name: /Hartono Wijaya Kusuma/ }).click();
      await page.locator(".client-pulse").getByText(/Evidence · \d+ cited records/).first().click();
      await page.getByRole("button", { name: /Open evidence .*LTV_2025_12_31/ }).first().click();
      const surface = page.locator(".work-surface");
      await expect(surface).toHaveCSS("transform", "matrix(1, 0, 0, 1, 0, 0)");
      const bounds = await surface.boundingBox();
      expect(bounds?.x).toBeGreaterThanOrEqual(0);
      expect((bounds?.x ?? 0) + (bounds?.width ?? 0)).toBeLessThanOrEqual(viewport.width);
      await page.screenshot({ path: "demo/screenshots/05-responsive-1000-drawer.png", fullPage: true });
    }
  }
});

test("architecture tells the demonstrated-versus-target story", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/architecture");
  await expect(page.getByRole("heading", { name: "Trust is a sequence, not a disclaimer." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Visible in the prototype" })).toBeVisible();
  await expect(page.getByText(/not claimed as present in the prototype/i)).toBeVisible();
  await page.screenshot({ path: "demo/screenshots/06-target-architecture.png", fullPage: true });
});

test("deep cases preserve client context and reporting language", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  await expect(page.getByText("Generated · attention")).toBeVisible();

  await page.getByRole("button", { name: "Cheung", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Cheung Kwok Wing", exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/rising yields/i).first()).toBeVisible();
  await page.getByRole("button", { name: "Review Client-Ready View" }).click();
  await expect(
    page.getByRole("heading", { name: "Client reporting language · Traditional Chinese" }),
  ).toBeVisible();
  await expect(page.getByText(/cached \/ offline mode/i)).toBeVisible();
  await page.screenshot({ path: "demo/screenshots/07-cheung-client-ready.png", fullPage: true });

  await page.getByRole("button", { name: "Close work surface" }).click();
  await page.getByRole("button", { name: /Margarethe Voss-Brenner/ }).click();
  await expect(
    page.getByRole("heading", { name: "Margarethe Voss-Brenner", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".client-pulse").getByText(/EUR 3,400,000|EUR 3\.4m/).first()).toBeVisible();
  await page.getByRole("button", { name: "Review Client-Ready View" }).click();
  await expect(
    page.getByRole("heading", { name: "Client reporting language · German" }),
  ).toBeVisible();
  await page.screenshot({ path: "demo/screenshots/08-margarethe-client-ready.png", fullPage: true });
});

test("core workbench makes no external network requests", async ({ page }) => {
  const externalRequests: string[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.protocol.startsWith("http") && url.hostname !== "127.0.0.1") {
      externalRequests.push(request.url());
    }
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Priority Queue" })).toBeVisible();
  await page.getByRole("button", { name: "Cheung", exact: true }).click();
  await page.getByRole("button", { name: "Review Client-Ready View" }).click();
  await expect(page.getByText(/cached \/ offline mode/i)).toBeVisible();
  expect(externalRequests).toEqual([]);
});

test("local analysis upload explains formats and Gemini availability", async ({ page }) => {
  await page.route("**/api/analysis/health", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ status: "ready", geminiConfigured: false }),
  }));
  await page.goto("/");
  await page.getByRole("button", { name: "Upload & analyse" }).click();
  await expect(page.getByRole("heading", { name: "Analyse a customer Book" })).toBeVisible();
  await expect(page.getByText(/CSV\/JSON files or an Excel workbook/i)).toBeVisible();
  await expect(page.getByText(/API key not configured/i)).toBeVisible();
  await expect(page.getByRole("button", { name: "Upload & analyse automatically" })).toBeEnabled();
  await page.getByRole("button", { name: "Cancel" }).click();
  await expect(page.getByRole("heading", { name: "Analyse a customer Book" })).not.toBeAttached();
});
