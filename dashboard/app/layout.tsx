import type { Metadata } from "next";
import { Inter, Geist_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "AgentSudo - The Permission Layer for AI Agents",
    template: "%s | AgentSudo",
  },
  description: "AgentSudo is a lightweight permission engine for AI agents. Enforce scopes, approvals, and safe tool use across LangChain, LlamaIndex, FastAPI, and custom agents.",
  keywords: ["AI agents", "permissions", "security", "Python", "LangChain", "LlamaIndex", "FastAPI", "LLM", "authorization", "IAM", "audit trail", "human-in-the-loop"],
  authors: [{ name: "xywa23", url: "https://github.com/xywa23" }],
  creator: "xywa23",
  icons: {
    icon: "/icon.png",
    apple: "/apple-icon.png",
  },
  openGraph: {
    title: "AgentSudo - The Permission Layer for AI Agents",
    description: "Like Auth0, but for LLMs. Enforce scopes, approvals, and safe tool use across LangChain, LlamaIndex, FastAPI, and custom agents.",
    url: "https://agentsudo.dev",
    siteName: "AgentSudo",
    images: [
      {
        url: "/og-image.png",
        width: 2800,
        height: 1512,
        alt: "AgentSudo - The sudo command for AI agents",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AgentSudo - The Permission Layer for AI Agents",
    description: "Like Auth0, but for LLMs. Enforce scopes, approvals, and safe tool use across LangChain, LlamaIndex, and FastAPI.",
    images: ["/og-image.png"],
    creator: "@xywa23",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  metadataBase: new URL("https://agentsudo.dev"),
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
