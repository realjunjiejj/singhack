import { NextResponse } from "next/server";

const ENGINE_URL = process.env.JB_CLARITY_ENGINE_URL ?? "http://127.0.0.1:8000";

export async function GET() {
  try {
    const response = await fetch(`${ENGINE_URL}/health`, { cache: "no-store", signal: AbortSignal.timeout(4_000) });
    const body = await response.json();
    return NextResponse.json(body, { status: response.status });
  } catch {
    return NextResponse.json(
      { status: "unavailable", geminiConfigured: false, detail: "The local analysis engine is not running." },
      { status: 503 },
    );
  }
}
