"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { createJob } from "@/lib/api";
import { Briefcase, Building, MapPin, AlignLeft, Info } from "lucide-react";

export default function CreateJobPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    title: "",
    company_name: "",
    location: "",
    description: "",
    work_type: "office",
    experience_level: "mid",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.id]: e.target.value });
  };

  const handleSelectChange = (key: string, value: string) => {
    setFormData((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    
    const token = localStorage.getItem("accessToken");
    if (!token) {
      setError("Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.");
      setIsLoading(false);
      return;
    }

    try {
      await createJob(token, formData);
      alert("İlan başarıyla oluşturuldu! Özellikler yapay zeka tarafından analiz ediliyor.");
      router.push("/jobs");
    } catch (err: any) {
      setError(err.message || "Bir hata oluştu.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 max-w-3xl">
      <Card className="shadow-lg border-t-4 border-t-primary">
        <CardHeader className="space-y-1">
          <div className="flex items-center space-x-2">
            <Briefcase className="h-6 w-6 text-primary" />
            <CardTitle className="text-2xl font-bold">Yeni İş İlanı Oluştur</CardTitle>
          </div>
          <CardDescription>
            İş ilanınızın detaylarını girin. İlanınızın eğitim ve yetenek gereksinimleri yapay zeka tarafından otomatik olarak çıkarılacaktır.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form id="create-job-form" onSubmit={handleSubmit} className="space-y-6">
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="title" className="flex items-center gap-2">
                    <Briefcase className="h-4 w-4 text-muted-foreground" />
                    Pozisyon Başlığı <span className="text-red-500">*</span>
                  </Label>
                  <Input 
                    id="title" 
                    placeholder="örn. Senior Frontend Developer" 
                    value={formData.title} 
                    onChange={handleChange} 
                    required 
                    className="focus-visible:ring-primary"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="company_name" className="flex items-center gap-2">
                    <Building className="h-4 w-4 text-muted-foreground" />
                    Şirket Adı <span className="text-red-500">*</span>
                  </Label>
                  <Input 
                    id="company_name" 
                    placeholder="örn. Tech Corp" 
                    value={formData.company_name} 
                    onChange={handleChange} 
                    required 
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="location" className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    Lokasyon
                  </Label>
                  <Input 
                    id="location" 
                    placeholder="örn. İstanbul veya Uzaktan" 
                    value={formData.location} 
                    onChange={handleChange} 
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="work_type" className="flex items-center gap-2">
                    Çalışma Şekli
                  </Label>
                  <Select value={formData.work_type} onValueChange={(val) => handleSelectChange("work_type", val)}>
                    <SelectTrigger id="work_type">
                      <SelectValue placeholder="Seçiniz" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="office">Ofisten</SelectItem>
                      <SelectItem value="hybrid">Hibrit</SelectItem>
                      <SelectItem value="remote">Uzaktan</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="experience_level" className="flex items-center gap-2">
                  Deneyim Seviyesi
                </Label>
                <Select value={formData.experience_level} onValueChange={(val) => handleSelectChange("experience_level", val)}>
                  <SelectTrigger id="experience_level">
                    <SelectValue placeholder="Seçiniz" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="entry">Başlangıç (Junior)</SelectItem>
                    <SelectItem value="mid">Orta Düzey (Mid-Level)</SelectItem>
                    <SelectItem value="senior">Kıdemli (Senior)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description" className="flex items-center gap-2">
                  <AlignLeft className="h-4 w-4 text-muted-foreground" />
                  İş Açıklaması ve Gereksinimler
                </Label>
                <Textarea 
                  id="description" 
                  placeholder="İşin sorumlulukları, aranan yetenekler ve diğer detayları buraya yazınız..." 
                  value={formData.description} 
                  onChange={handleChange} 
                  rows={6}
                  className="resize-y"
                />
                <p className="text-xs text-muted-foreground flex items-start gap-1 mt-1">
                  <Info className="h-3 w-3 mt-0.5 inline-block shrink-0" />
                  Yapay zeka asistanımız, bu açıklama metninden zorunlu eğitim ve temel becerileri otomatik olarak çıkaracaktır. Lütfen olabildiğince detaylı yazınız.
                </p>
              </div>
            </div>

            {error && (
              <div className="p-3 rounded-md bg-destructive/10 text-destructive text-sm font-medium border border-destructive/20">
                {error}
              </div>
            )}
          </form>
        </CardContent>
        <CardFooter className="flex justify-end gap-3 border-t bg-muted/20 py-4">
          <Button variant="outline" type="button" onClick={() => router.back()}>
            İptal
          </Button>
          <Button type="submit" form="create-job-form" disabled={isLoading} className="gap-2">
            {isLoading ? (
               <>
                 <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
                 Oluşturuluyor...
               </>
            ) : (
              <>
                 <Briefcase className="h-4 w-4" />
                 İlanı Yayınla
              </>
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
