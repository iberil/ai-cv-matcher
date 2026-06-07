"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Loader2 } from "lucide-react";

export default function EditJobPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [jobId, setJobId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: "",
    company_name: "",
    description: "",
    requirements: "",
    skills_required: "",
    location: "",
    work_type: "",
    job_type: "",
    experience_level: "",
    salary_min: "",
    salary_max: "",
    sector: "",
  });

  useEffect(() => {
    const getParams = async () => {
      const resolvedParams = await params;
      setJobId(resolvedParams.id);
    };
    getParams();
  }, [params]);

  useEffect(() => {
    if (!jobId) return;

    const fetchJob = async () => {
      try {
        const response = await fetch(`https://ai-cv-matcher-5sui.onrender.com/api/v1/jobs/${jobId}`);
        const job = await response.json();
        
        setFormData({
          title: job.title || "",
          company_name: job.company_name || "",
          description: job.description || "",
          requirements: job.requirements || "",
          skills_required: job.skills_required || "",
          location: job.location || "",
          work_type: job.work_type || "",
          job_type: job.job_type || "",
          experience_level: job.experience_level || "",
          salary_min: job.salary_min?.toString() || "",
          salary_max: job.salary_max?.toString() || "",
          sector: job.sector || "",
        });
      } catch (error) {
        alert("İş ilanı yüklenemedi");
      } finally {
        setIsFetching(false);
      }
    };

    fetchJob();
  }, [jobId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const token = localStorage.getItem("accessToken");
      if (!token) {
        alert("Lütfen giriş yapın");
        router.push("/login");
        return;
      }

      const response = await fetch(`https://ai-cv-matcher-5sui.onrender.com/api/v1/jobs/${jobId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          ...formData,
          salary_min: formData.salary_min ? parseFloat(formData.salary_min) : null,
          salary_max: formData.salary_max ? parseFloat(formData.salary_max) : null,
        }),
      });

      if (!response.ok) {
        throw new Error("İş ilanı güncellenemedi");
      }

      alert("İş ilanı başarıyla güncellendi!");
      router.push(`/jobs/${jobId}`);
    } catch (error: any) {
      alert(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (isFetching) {
    return (
      <div className="container mx-auto py-8 text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 md:px-0 max-w-3xl">
      <Card>
        <CardHeader>
          <CardTitle>İş İlanını Düzenle</CardTitle>
          <CardDescription>İş ilanı bilgilerini güncelleyin</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="title">Pozisyon Adı *</Label>
              <Input
                id="title"
                required
                value={formData.title}
                onChange={(e) => handleChange("title", e.target.value)}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="company_name">Şirket Adı *</Label>
              <Input
                id="company_name"
                required
                value={formData.company_name}
                onChange={(e) => handleChange("company_name", e.target.value)}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Açıklama</Label>
              <textarea
                id="description"
                className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2"
                value={formData.description}
                onChange={(e) => handleChange("description", e.target.value)}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="requirements">Gereksinimler</Label>
              <textarea
                id="requirements"
                className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2"
                value={formData.requirements}
                onChange={(e) => handleChange("requirements", e.target.value)}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="skills_required">Gerekli Beceriler</Label>
              <Input
                id="skills_required"
                value={formData.skills_required}
                onChange={(e) => handleChange("skills_required", e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>Konum</Label>
                <Input
                  value={formData.location}
                  onChange={(e) => handleChange("location", e.target.value)}
                />
              </div>

              <div className="grid gap-2">
                <Label>Sektör</Label>
                <Input
                  value={formData.sector}
                  onChange={(e) => handleChange("sector", e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="grid gap-2">
                <Label>Çalışma Türü</Label>
                <Select value={formData.work_type} onValueChange={(value) => handleChange("work_type", value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="office">Ofiste</SelectItem>
                    <SelectItem value="remote">Uzaktan</SelectItem>
                    <SelectItem value="hybrid">Hibrit</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label>İş Türü</Label>
                <Select value={formData.job_type} onValueChange={(value) => handleChange("job_type", value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="full-time">Tam Zamanlı</SelectItem>
                    <SelectItem value="part-time">Yarı Zamanlı</SelectItem>
                    <SelectItem value="contract">Sözleşmeli</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label>Deneyim</Label>
                <Select value={formData.experience_level} onValueChange={(value) => handleChange("experience_level", value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="entry">Giriş</SelectItem>
                    <SelectItem value="mid">Orta</SelectItem>
                    <SelectItem value="senior">Kıdemli</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>Min. Maaş (TL)</Label>
                <Input
                  type="number"
                  value={formData.salary_min}
                  onChange={(e) => handleChange("salary_min", e.target.value)}
                />
              </div>

              <div className="grid gap-2">
                <Label>Max. Maaş (TL)</Label>
                <Input
                  type="number"
                  value={formData.salary_max}
                  onChange={(e) => handleChange("salary_max", e.target.value)}
                />
              </div>
            </div>

            <div className="flex gap-4 pt-4">
              <Button type="submit" disabled={isLoading} className="flex-1">
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isLoading ? "Güncelleniyor..." : "Güncelle"}
              </Button>
              <Button type="button" variant="outline" onClick={() => router.back()}>
                İptal
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
