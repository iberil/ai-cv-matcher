import React from "react";

// Bu, (auth) grubundaki tüm sayfalar için geçerli olacak layout'tur.
// Amacı, bu sayfalarda ana Navbar'ın görünmesini engellemektir.
export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    // Sadece gelen içeriği (children) render et, başka bir şey ekleme.
    <main>{children}</main>
  );
}
