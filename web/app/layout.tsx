import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ChargePilot — Austin EV Network Optimizer',
  description: 'AI-powered EV charging network optimizer for Austin, TX',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Azeret+Mono:wght@400;500;600&family=Outfit:wght@300;400;500;600;700&family=Syne:wght@600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="h-full bg-deep text-white antialiased font-body">{children}</body>
    </html>
  );
}
