import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, test, vi } from "vitest";
import { DatasetUpload } from "@/components/upload/DatasetUpload";

test("uploads selected data and adopts the completed intelligence run", async () => {
  const run = { schemaVersion: "1.0.0", runId: "RUN-TEST", generatedAt: "2026-09-05T00:00:00Z", status: "completed", deepFocus: ["hidden-risk", "prioritisation"], diagnostics: [], agentReports: [], workbench: { meta: {} } };
  const fetchMock = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({ status: "ready", geminiConfigured: false }), { status: 200 }))
    .mockResolvedValueOnce(new Response(JSON.stringify(run), { status: 200 }));
  vi.stubGlobal("fetch", fetchMock);
  const onComplete = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();

  render(<DatasetUpload onClose={vi.fn()} onComplete={onComplete} />);
  await screen.findByText("Ready");
  await user.upload(screen.getByLabelText(/choose files/i), new File(["client_id\nCL-1"], "clients.csv", { type: "text/csv" }));
  await user.click(screen.getByRole("button", { name: /upload & analyse automatically/i }));

  await waitFor(() => expect(onComplete).toHaveBeenCalledWith(run));
  expect(fetchMock).toHaveBeenLastCalledWith("/api/analysis", expect.objectContaining({ method: "POST", body: expect.any(FormData) }));
  vi.unstubAllGlobals();
});
