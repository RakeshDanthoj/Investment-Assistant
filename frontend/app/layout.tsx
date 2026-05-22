import type { Metadata } from "next";
import { Inter, Playfair_Display, DM_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
});

const dmMono = DM_Mono({
  weight: ["400", "500"],
  subsets: ["latin"],
  variable: "--font-dm-mono",
});

export const metadata: Metadata = {
  title: "FinnWise",
  description: "Event intelligence for Indian markets",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${playfair.variable} ${dmMono.variable}`}
    >
      <body className="h-svh overflow-hidden bg-background antialiased">
        {children}
      </body>
    </html>
  );
}
