import type { Metadata } from "next";
import "@/styles/tokens.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "Julius Bär Clarity · RM Intelligence Workbench",
  description: "Turn insight into client-ready actions, with the Relationship Manager in control.",
  icons: { icon: "/julius-baer-logo.png" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
