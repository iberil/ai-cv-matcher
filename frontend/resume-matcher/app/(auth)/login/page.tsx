"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Users, Building, ArrowLeft } from "lucide-react";
import { registerUser, loginUser } from "@/lib/api";

type Role = "aday" | "isveren";
type FormType = "login" | "register";

const getApiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'https://ai-cv-matcher-5sui.onrender.com/api/v1';

export default function AuthPage() {
  const router = useRouter();

  const [role, setRole] = useState<Role | null>(null);
  const [formType, setFormType] = useState<FormType>("login");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [dateOfBirth, setDateOfBirth] = useState("");
  const [profession, setProfession] = useState("");

  const clearFormFields = () => {
    setFullName("");
    setEmail("");
    setPassword("");

    setDateOfBirth("");
    setProfession("");
    setError(null);
  };

  const handleBackToSelection = () => {
    setRole(null);
    clearFormFields();
  };

  const switchFormType = (type: FormType) => {
    setFormType(type);
    clearFormFields();
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!role) return;
    setIsLoading(true);
    setError(null);
    try {
      const userData = {
        fullName,
        email,
        password,
        userRole: role,

        dateOfBirth: dateOfBirth || undefined,
        profession: profession || undefined,
      };

      await registerUser(userData);
      alert("Kayıt başarıyla tamamlandı! Şimdi giriş yapabilirsiniz.");
      switchFormType("login");
    } catch (err: any) {
      setError(err.message || "Bir hata oluştu.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const result = await loginUser({ email, password });
      localStorage.setItem("accessToken", result.access_token);
      
      const apiUrl = getApiUrl();
      const userResponse = await fetch(`${apiUrl}/users/me`, {
        headers: { Authorization: `Bearer ${result.access_token}` }
      });
      
      if (userResponse.ok) {
        const user = await userResponse.json();
        localStorage.setItem("userId", user.id.toString());
        
        if (user.user_role === "isveren") {
          alert("Giriş başarılı! Dashboard'a yönlendiriliyorsunuz.");
          router.push("/dashboard");
        } else {
          alert("Giriş başarılı! İş ilanları sayfasına yönlendiriliyorsunuz.");
          router.push("/jobs");
        }
      } else {
        router.push("/jobs");
      }
    } catch (err: any) {
      setError(err.message || "Bir hata oluştu.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!role) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <Card className="w-full max-w-md text-center">
          <CardHeader>
            <CardTitle className="text-2xl">Hoş Geldiniz!</CardTitle>
            <CardDescription>
              Lütfen rolünüzü seçerek devam edin.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={() => setRole("aday")}
              className="group flex flex-col items-center justify-center p-6 border rounded-lg hover:bg-gray-100 transition-colors"
            >
              <Users className="h-12 w-12 text-gray-400 group-hover:text-blue-600" />
              <span className="mt-2 font-semibold text-lg">İş Arayanım</span>
            </button>
            <button
              onClick={() => setRole("isveren")}
              className="group flex flex-col items-center justify-center p-6 border rounded-lg hover:bg-gray-100 transition-colors"
            >
              <Building className="h-12 w-12 text-gray-400 group-hover:text-blue-600" />
              <span className="mt-2 font-semibold text-lg">İş Verenim</span>
            </button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 py-12">
      <Card className="w-full max-w-md relative">
        <Button
          onClick={handleBackToSelection}
          variant="ghost"
          size="icon"
          className="absolute top-4 left-4"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <CardHeader className="text-center pt-12">
          <CardTitle className="text-2xl">
            {role === "aday" ? "Aday" : "İş Veren"}{" "}
            {formType === "login" ? "Girişi" : "Kaydı"}
          </CardTitle>
          <CardDescription>
            {formType === "login"
              ? "Devam etmek için bilgilerinizi girin."
              : "Hesap oluşturmak için bilgilerinizi girin."}
          </CardDescription>
        </CardHeader>

        <CardContent>
          {error && (
            <p className="text-sm font-medium text-red-500 text-center -mt-2 mb-4">
              {error}
            </p>
          )}
        </CardContent>

        {formType === "login" && (
          <form onSubmit={handleLogin}>
            <CardContent className="grid gap-4">
              <div className="grid gap-2">
                <Label htmlFor="login-email">E-posta</Label>
                <Input
                  id="login-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="login-password">Şifre</Label>
                <Input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </CardContent>
            <CardFooter className="flex flex-col">
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Giriş Yapılıyor..." : "Giriş Yap"}
              </Button>
              <Button
                type="button"
                onClick={() => switchFormType("register")}
                variant="link"
                className="mt-4"
              >
                Hesabın yok mu? Kayıt Ol
              </Button>
            </CardFooter>
          </form>
        )}

        {formType === "register" && (
          <form onSubmit={handleRegister}>
            <CardContent className="grid gap-3">
              <div className="grid gap-2">
                <Label htmlFor="full-name">
                  {role === "aday" ? "İsim Soyisim" : "Şirket Adı"}
                </Label>
                <Input
                  id="full-name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="register-email">E-posta</Label>
                <Input
                  id="register-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              {role === "aday" && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="date-of-birth">Doğum Tarihi</Label>
                    <Input
                      id="date-of-birth"
                      type="date"
                      value={dateOfBirth}
                      onChange={(e) => setDateOfBirth(e.target.value)}
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="profession">Meslek</Label>
                    <Input
                      id="profession"
                      value={profession}
                      onChange={(e) => setProfession(e.target.value)}
                    />
                  </div>
                </div>
              )}
              <div className="grid gap-2">
                <Label htmlFor="register-password">Şifre</Label>
                <Input
                  id="register-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </CardContent>
            <CardFooter className="flex flex-col">
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Kaydediliyor..." : "Hesap Oluştur"}
              </Button>
              <Button
                type="button"
                onClick={() => switchFormType("login")}
                variant="link"
                className="mt-4"
              >
                Zaten bir hesabın var mı? Giriş Yap
              </Button>
            </CardFooter>
          </form>
        )}
      </Card>
    </div>
  );
}
