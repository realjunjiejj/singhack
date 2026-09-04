import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";

/**
 * The Workbench must render a Book it has never seen.
 *
 * The second Book is supplied by intercepting the artifact request rather than
 * by swapping the file the dev server has already cached. That keeps this
 * suite completely isolated: it cannot disturb the SingHacks golden path, and
 * it does not depend on which spec Playwright decides to run first.
 */
// Playwright runs with its config directory (web/) as the working directory.
const WEB_ROOT = process.cwd();
const SECOND_BOOK = path.resolve(WEB_ROOT, "..", "artifacts", "second-book", "workbench.json");

function secondBookArtifact(): string {
  if (!existsSync(SECOND_BOOK)) {
    throw new Error(
      `Second Book artifact missing at ${SECOND_BOOK}. Build it with: ` +
        "python -m jb_clarity.cli build --data artifacts/second-book/data " +
        "--as-of 2026-03-31 --output artifacts/second-book/workbench.json",
    );
  }
  return readFileSync(SECOND_BOOK, "utf8");
}

/** Serve the second Book for this page only. */
async function useSecondBook(page: Page): Promise<void> {
  const body = secondBookArtifact();
  await page.route("**/data/workbench.json", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body }),
  );
}

test("a non-demonstration Book renders with real featured cases", async ({ page }) => {
  await useSecondBook(page);
  await page.goto("/");

  // The Book's own identity, not the demonstration Book's.
  await expect(page.getByText("Ingrid Solberg")).toBeVisible();
  await expect(page.getByText("4/4")).toBeVisible();

  // Shortcuts are derived from the artifact, not from hardcoded identifiers.
  await expect(page.locator('[aria-label="Featured cases"]')).toBeVisible();
  await expect(page.locator('[aria-label="Demo cases"]')).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Hartono", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Cheung", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Alarcon", exact: true })).toBeVisible();

  await page.screenshot({ path: "demo/screenshots/09-second-book-queue.png" });
});

test("a second-Book case opens evidence drawn from its own records", async ({ page }) => {
  await useSecondBook(page);
  await page.goto("/");

  await page.getByRole("button", { name: "Roth", exact: true }).click();
  await expect(page.getByText("Anselm Roth").first()).toBeVisible();
  await expect(page.getByText("MW-C-100", { exact: false }).first()).toBeVisible();

  // Evidence identifiers belong to this Book, not the demonstration one.
  await expect(
    page.getByRole("button", { name: /Open evidence EV-MW-/ }).first(),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: /Open evidence EV-CL-/ })).toHaveCount(0);

  await page.getByRole("button", { name: /Open evidence EV-MW-/ }).first().click();

  await page.screenshot({ path: "demo/screenshots/10-second-book-evidence.png" });
});

test("the second Book reports its own snapshot count", async ({ page }) => {
  await useSecondBook(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Alarcon", exact: true }).click();

  // Four snapshots, not the demonstration Book's five.
  await expect(page.getByText("31 Mar 2026").first()).toBeVisible();
  await expect(page.getByText(/five supplied snapshots/)).toHaveCount(0);
});

test("the second Book makes no external network request", async ({ page }) => {
  const external: string[] = [];
  page.on("request", (request) => {
    const url = request.url();
    if (!/^https?:\/\/(localhost|127\.0\.0\.1)/.test(url) && !url.startsWith("data:")) {
      external.push(url);
    }
  });
  await useSecondBook(page);
  await page.goto("/");
  await page.waitForLoadState("networkidle");
  expect(external).toEqual([]);
});
