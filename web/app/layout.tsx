import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ChargePilot — Austin EV Network Optimizer',
  description: 'AI-powered EV charging network optimizer for Austin, TX',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full bg-gray-950 text-white antialiased">{children}</body>
    </html>
  );
}
