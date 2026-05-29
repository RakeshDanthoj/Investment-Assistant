export default function MirrorLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <div className="min-h-0 min-w-0 flex-1">{children}</div>;
}
