import { editorialFontVariables } from "@/lib/fonts/editorial";

export default function LensLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <div className={`min-h-0 min-w-0 flex-1 ${editorialFontVariables}`}>{children}</div>;
}
