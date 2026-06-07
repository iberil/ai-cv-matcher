"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Building, Globe, Users, MapPin, Briefcase, Loader2 } from "lucide-react";

interface CompanyProfile {
  full_name: string;
  email: string;
  company_description?: string;
  company_website?: string;
  company_size?: string;
  company_sector?: string;
  company_location?: string;
}

interface JobPosting {
  id: number;
  title: string;
  location?: string;
  created_at: string;
  is_active: boolean;
}

export default function EmployerProfilePage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [profile, setProfile] = useState<CompanyProfile>({
    full_name: "",
    email: "",
    company_description: "",
    company_website: "",
    company_size: "",
    company_sector: "",
    company_location: "",
  });
  const [jobs, setJobs] = useState<JobPosting[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem("accessToken");
        if (!token) {
          router.push("/login");
          return;
        }

        // Profil bilgilerini al
        const profileResponse = await fetch("https://ai-cv-matcher-5sui.onrender.com/api/v1/users/me", {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (profileResponse.ok) {
          const data = await profileResponse.json();
          setProfile(data);
        }

        // Aktif ilanları al
        const jobsResponse = await fetch("https://ai-cv-matcher-5sui.onrender.com/api/v1/jobs/my-jobs", {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (jobsResponse.ok) {
          const jobsData = await jobsResponse.json();
          setJobs(jobsData.filter((job: JobPosting) => job.is_active));
        }
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [router]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const token = localStorage.getItem("accessToken");
      const response = await fetch("https://ai-cv-matcher-5sui.onrender.com/api/v1/users/me", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          full_name: profile.full_name,
          company_description: profile.company_description,
          company_website: profile.company_website,
          company_size: profile.company_size,
          company_sector: profile.company_sector,
          company_location: profile.company_location,
        })
      });

      if (response.ok) {
        alert("Profil başarıyla güncellendi!");
      }
    } catch (error) {
      alert("Güncelleme başarısız");
    } finally {
      setIsSaving(false);
    }
  };

  const handleChange = (field: keyof CompanyProfile, value: string) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 md:px-0">
      <h1 className="text-4xl font-bold mb-8">Şirket Profili</h1>

      <div className="grid gap-8 md:grid-cols-3">
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Şirket Bilgileri</CardTitle>
              <CardDescription>Şirketiniz hakkında bilgileri güncelleyin</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                <Label htmlFor="company_name">Şirket Adı</Label>
                <Input
                  id="company_name"
                  value={profile.full_name}
                  onChange={(e) => handleChange("full_name", e.target.value)}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="email">E-posta</Label>
                <Input
                  id="email"
                  type="email"
                  value={profile.email}
                  disabled
                  className="bg-gray-50"
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="description">Şirket Açıklaması</Label>
                <textarea
                  id="description"
                  className="min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2"
                  value={profile.company_description || ""}
                  onChange={(e) => handleChange("company_description", e.target.value)}
                  placeholder="Şirketiniz hakkında kısa bir açıklama..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="website">Website</Label>
                  <Input
                    id="website"
                    value={profile.company_website || ""}
                    onChange={(e) => handleChange("company_website", e.target.value)}
                    placeholder="https://sirket.com"
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="location">Konum</Label>
                  <Input
                    id="location"
                    value={profile.company_location || ""}
                    onChange={(e) => handleChange("company_location", e.target.value)}
                    placeholder="İstanbul, Türkiye"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="sector">Sektör</Label>
                  <Input
                    id="sector"
                    value={profile.company_sector || ""}
                    onChange={(e) => handleChange("company_sector", e.target.value)}
                    placeholder="Teknoloji"
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="size">Çalışan Sayısı</Label>
                  <Input
                    id="size"
                    value={profile.company_size || ""}
                    onChange={(e) => handleChange("company_size", e.target.value)}
                    placeholder="50-100"
                  />
                </div>
              </div>

              <Button onClick={handleSave} disabled={isSaving} className="w-full">
                {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isSaving ? "Kaydediliyor..." : "Değişiklikleri Kaydet"}
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Şirket Özeti</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center text-sm">
                <Building className="mr-2 h-4 w-4 text-muted-foreground" />
                <span className="font-medium">{profile.full_name}</span>
              </div>
              {profile.company_location && (
                <div className="flex items-center text-sm">
                  <MapPin className="mr-2 h-4 w-4 text-muted-foreground" />
                  <span>{profile.company_location}</span>
                </div>
              )}
              {profile.company_website && (
                <div className="flex items-center text-sm">
                  <Globe className="mr-2 h-4 w-4 text-muted-foreground" />
                  <a href={profile.company_website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    Website
                  </a>
                </div>
              )}
              {profile.company_size && (
                <div className="flex items-center text-sm">
                  <Users className="mr-2 h-4 w-4 text-muted-foreground" />
                  <span>{profile.company_size} çalışan</span>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Aktif İlanlar</CardTitle>
              <CardDescription>{jobs.length} aktif ilan</CardDescription>
            </CardHeader>
            <CardContent>
              {jobs.length === 0 ? (
                <p className="text-sm text-muted-foreground text-center py-4">
                  Henüz aktif ilan yok
                </p>
              ) : (
                <div className="space-y-3">
                  {jobs.slice(0, 5).map((job) => (
                    <div
                      key={job.id}
                      className="flex items-start justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                      onClick={() => router.push(`/jobs/${job.id}`)}
                    >
                      <div className="flex-1">
                        <p className="font-medium text-sm">{job.title}</p>
                        {job.location && (
                          <p className="text-xs text-muted-foreground">{job.location}</p>
                        )}
                      </div>
                      <Briefcase className="h-4 w-4 text-muted-foreground" />
                    </div>
                  ))}
                  {jobs.length > 5 && (
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => router.push("/dashboard")}
                    >
                      Tümünü Gör ({jobs.length})
                    </Button>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
