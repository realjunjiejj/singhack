import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 300;

const ENGINE_URL = process.env.JB_CLARITY_ENGINE_URL ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const response = await fetch(`${ENGINE_URL}/analyse`, {
      method: "POST",
      body: formData,
      signal: AbortSignal.timeout(300_000),
    });
    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: { "content-type": response.headers.get("content-type") ?? "application/json" },
    });
  } catch (error) {
    const detail = error instanceof Error && error.name === "TimeoutError"
      ? "Analysis exceeded the five-minute local timeout."
      : "The local analysis engine is unavailable. Start npm run dev:full and try again.";
    return NextResponse.json({ detail }, { status: 503 });
  }
}
