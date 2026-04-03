import type { Metadata } from "next";
import AuthLayout from "@/components/shared/AuthLayout";
import { ServiceWorkerProvider } from "@/components/ServiceWorkerProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "TaskStars",
  description: "Level up your life",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <body className="min-h-full bg-black text-white selection:bg-yellow-500 selection:text-black font-sans">
        <ServiceWorkerProvider>
          <AuthLayout>
            {children}
          </AuthLayout>
        </ServiceWorkerProvider>
      </body>
    </html>
  );
}
