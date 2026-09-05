import type { Metadata } from "next";
import "@/styles/tokens.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "AAActual Intelligence · RM Intelligence Workbench",
  description: "Turn insight into client-ready actions, with the Relationship Manager in control.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
