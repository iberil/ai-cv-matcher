"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { LogOut, MessageCircle } from "lucide-react";
import NotificationBell from "@/components/NotificationBell";

function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [userRole, setUserRole] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");
  const [unreadMessagesCount, setUnreadMessagesCount] = useState(0);

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem("accessToken");
      if (!token) return;

      try {
        const response = await fetch("http://127.0.0.1:8000/api/v1/users/me", {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (response.ok) {
          const user = await response.json();
          setUserRole(user.user_role);
          setUserName(user.full_name);
        }
      } catch (error) {
        console.error(error);
      }
    };

    const fetchUnreadMessages = async () => {
      const token = localStorage.getItem("accessToken");
      if (!token) return;

      try {
        const response = await fetch("http://127.0.0.1:8000/api/v1/messages/conversations", {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          const conversations = await response.json();
          const totalUnread = conversations.reduce((acc: number, conv: any) => acc + conv.unread_count, 0);
          setUnreadMessagesCount(totalUnread);
        }
      } catch (error) {
        console.error("Mesajlar alınamadı:", error);
      }
    };

    fetchUser();
    fetchUnreadMessages();
    
    // Poll for unread messages every 2 minutes
    const interval = setInterval(fetchUnreadMessages, 120000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("userId");
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center mx-auto px-4 md:px-8">
        <div className="mr-4 flex items-center">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <span className="font-bold">CV-Matcher</span>
          </Link>
          <nav className="flex items-center space-x-6 text-sm font-medium">
            {userRole === "isveren" ? (
              <>
                <Link
                  href="/dashboard"
                  className={`transition-colors hover:text-foreground/80 ${
                    pathname === "/dashboard" ? "text-foreground" : "text-foreground/60"
                  }`}
                >
                  İlanlarım
                </Link>
                <Link
                  href="/employer-profile"
                  className={`transition-colors hover:text-foreground/80 ${
                    pathname === "/employer-profile" ? "text-foreground" : "text-foreground/60"
                  }`}
                >
                  Şirket Hakkında
                </Link>
                <Link
                  href="/jobs"
                  className={`transition-colors hover:text-foreground/80 ${
                    pathname === "/jobs" ? "text-foreground" : "text-foreground/60"
                  }`}
                >
                  Tüm İlanlar
                </Link>
              </>
            ) : (
              <>
                <Link
                  href="/jobs"
                  className={`transition-colors hover:text-foreground/80 ${
                    pathname === "/jobs" ? "text-foreground" : "text-foreground/60"
                  }`}
                >
                  İş İlanları
                </Link>
                <Link
                  href="/profile"
                  className={`transition-colors hover:text-foreground/80 ${
                    pathname === "/profile" ? "text-foreground" : "text-foreground/60"
                  }`}
                >
                  Profilim
                </Link>
              </>
            )}
          </nav>
        </div>
        <div className="flex flex-1 items-center justify-end space-x-4">
          <div className="relative">
            <Link href="/messages">
              <Button variant="ghost" size="icon">
                <MessageCircle className="h-5 w-5" />
              </Button>
            </Link>
            {unreadMessagesCount > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-600 text-[10px] font-bold text-white">
                {unreadMessagesCount > 9 ? "9+" : unreadMessagesCount}
              </span>
            )}
          </div>
          <NotificationBell />
          {userName && (
            <span className="text-sm text-muted-foreground hidden sm:inline-block">{userName}</span>
          )}
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="h-4 w-4 mr-2" />
            <span className="hidden sm:inline-block">Çıkış</span>
          </Button>
        </div>
      </div>
    </header>
  );
}

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
    </div>
  );
}