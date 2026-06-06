import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-gray-50 to-gray-100 text-center p-4">
      <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-gray-900">
        Kariyerinize Yapay Zeka Dokunuşu
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-gray-600">
        CV-Matcher, özgeçmişinizi en uygun iş ilanlarıyla saniyeler içinde
        eşleştirir. Hayalinizdeki işe bir adım daha yaklaşın.
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-4">
        {/* 'İş İlanlarını Keşfet' butonunu kaldırdık */}
        <Button asChild size="lg">
          <Link href="/login">Giriş Yap / Kayıt Ol</Link>
        </Button>
      </div>
      <p className="mt-8 text-sm text-gray-500">
        İş ilanlarını görmek ve profilinizi oluşturmak için lütfen giriş yapın.
      </p>
    </div>
  );
}