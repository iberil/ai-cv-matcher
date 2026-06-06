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
import Link from "next/link";

export default function RegisterPage() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 py-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">Hesap Oluştur</CardTitle>
          <CardDescription>Başlamak için bilgilerinizi girin.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="first-name">İsim</Label>
              <Input id="first-name" placeholder="Adınız" required />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="last-name">Soyisim</Label>
              <Input id="last-name" placeholder="Soyadınız" required />
            </div>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email">E-posta</Label>
            <Input
              id="email"
              type="email"
              placeholder="ornek@mail.com"
              required
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="phone">Telefon</Label>
            <Input id="phone" type="tel" placeholder="555 123 4567" required />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="password">Şifre</Label>
            <Input id="password" type="password" required />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col">
          <Button className="w-full">Kayıt Ol</Button>
          <div className="mt-4 text-center text-sm">
            Zaten bir hesabın var mı?{" "}
            <Link href="/login" className="underline">
              Giriş Yap
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
