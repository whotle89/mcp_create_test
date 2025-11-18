import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Time Trade App",
  description: "Time trading application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
