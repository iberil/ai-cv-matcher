"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Briefcase, Users, Plus, Loader2, BarChart3 } from "lucide-react";

interface MyJob {
  id: number;
  title: string;
  company_name: string;
  location?: string;
  created_at: string;
  is_active: boolean;
}

export default function EmployerDashboard() {
  const router = useRouter();
  const [jobs, setJobs] = useState<MyJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchMyJobs = async () => {
      try {
        const token = localStorage.getItem("accessToken");
        if (!token) {
          router.push("/login");
          return;
        }

        const response = await fetch("https://ai-cv-matcher-5sui.onrender.com/api/v1/jobs/my-jobs", {
          headers: { Authorization: `Bearer ${token}` }
        });

        if (response.ok) {
          const data = await response.json();
          setJobs(data);
        }
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMyJobs();
  }, [router]);

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 md:px-0">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-4xl font-bold">İşveren Paneli</h1>
          <p className="text-muted-foreground mt-2">İş ilanlarınızı yönetin ve uygun adayları görün</p>
        </div>
        <Button onClick={() => router.push("/jobs/create")}>
          <Plus className="mr-2 h-4 w-4" />
          Yeni İlan Oluştur
        </Button>
      </div>

      {jobs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Briefcase className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
            <p className="text-muted-foreground mb-4">Henüz iş ilanınız yok</p>
            <Button onClick={() => router.push("/jobs/create")}>
              İlk İlanınızı Oluşturun
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <Card key={job.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="text-lg">{job.title}</CardTitle>
                <CardDescription>{job.company_name}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {job.location && (
                  <p className="text-sm text-muted-foreground">{job.location}</p>
                )}
                <div className="flex items-center justify-between">
                  <span className={`text-xs px-2 py-1 rounded ${job.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {job.is_active ? 'Aktif' : 'Pasif'}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(job.created_at).toLocaleDateString('tr-TR')}
                  </span>
                </div>
                <div className="flex gap-2">
                  <Button 
                    className="flex-1" 
                    variant="outline"
                    onClick={() => router.push(`/dashboard/jobs/${job.id}/matches`)}
                  >
                    <Users className="mr-2 h-4 w-4" />
                    Adaylar
                  </Button>
                  <Button 
                    className="flex-1"
                    variant="outline"
                    onClick={() => router.push(`/jobs/${job.id}/analysis`)}
                  >
                    <BarChart3 className="mr-2 h-4 w-4" />
                    Analiz
                  </Button>
                </div>
                <Button 
                  className="w-full"
                  onClick={() => router.push(`/jobs/${job.id}/edit`)}
                >
                  Düzenle
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
