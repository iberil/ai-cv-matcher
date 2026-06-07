"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { 
  MapPin, 
  Briefcase, 
  Clock, 
  DollarSign, 
  Building, 
  ArrowLeft,
  CheckCircle,
  Users,
  Edit,
  Trash2
} from "lucide-react";

interface JobDetail {
  id: number;
  title: string;
  company_name: string;
  description: string;
  requirements: string;
  skills_required: string;
  location: string;
  work_type: string;
  job_type: string;
  experience_level: string;
  salary_min: number;
  salary_max: number;
  sector: string;
  created_by: number;
}

export default function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [jobId, setJobId] = useState<string | null>(null);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [isOwner, setIsOwner] = useState(false);
  const [hasApplied, setHasApplied] = useState(false);
  const [isFavorite, setIsFavorite] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  useEffect(() => {
    const getParams = async () => {
      const resolvedParams = await params;
      setJobId(resolvedParams.id);
    };
    getParams();
  }, [params]);

  useEffect(() => {
    if (!jobId) return;
    
    const fetchJobDetail = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
        const response = await fetch(`${apiUrl}/jobs/${jobId}`);
        const jobData = await response.json();
        setJob(jobData);

        const token = localStorage.getItem("accessToken");
        if (token) {
          const userResponse = await fetch(`${apiUrl}/users/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (userResponse.ok) {
            const userData = await userResponse.json();
            setCurrentUserId(userData.id);
            setUserRole(userData.user_role);
            setIsOwner(userData.id === jobData.created_by);
            
            // Başvuru ve favori durumunu kontrol et
            if (userData.user_role === "aday") {
              const statusResponse = await fetch(`${apiUrl}/jobs/${jobId}/check-status`, {
                headers: { Authorization: `Bearer ${token}` }
              });
              if (statusResponse.ok) {
                const status = await statusResponse.json();
                setHasApplied(status.has_applied);
                setIsFavorite(status.is_favorite);
              }
            }
          }
        }
      } catch (err) {
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchJobDetail();
  }, [jobId]);

  const handleDelete = async () => {
    if (!confirm("Bu ilanı silmek istediğinizden emin misiniz?")) return;

    try {
      const token = localStorage.getItem("accessToken");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${apiUrl}/jobs/${jobId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        alert("İlan başarıyla silindi");
        router.push("/jobs");
      }
    } catch (err) {
      alert("Silme işlemi başarısız");
    }
  };

  const handleApply = async () => {
    setIsApplying(true);
    try {
      const token = localStorage.getItem("accessToken");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const response = await fetch(`${apiUrl}/jobs/${jobId}/apply`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        alert("Başvurunuz alındı!");
        setHasApplied(true);
      } else {
        const error = await response.json();
        alert(error.detail || "Başvuru başarısız");
      }
    } catch (err) {
      alert("Başvuru başarısız");
    } finally {
      setIsApplying(false);
    }
  };

  const handleToggleFavorite = async () => {
    try {
      const token = localStorage.getItem("accessToken");
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const method = isFavorite ? "DELETE" : "POST";
      const response = await fetch(`${apiUrl}/jobs/${jobId}/favorite`, {
        method,
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        setIsFavorite(!isFavorite);
        alert(isFavorite ? "Favorilerden çıkarıldı" : "Favorilere eklendi");
      }
    } catch (err) {
      alert("İşlem başarısız");
    }
  };

  if (isLoading || !job) {
    return <div className="container mx-auto py-8 px-4 text-center">Yükleniyor...</div>;
  }

  const skillsList = job.skills_required?.split(',').map(skill => skill.trim()) || [];
  const requirementsList = job.requirements?.split('\n').filter(req => req.trim() !== '').map(req => req.trim()) || [];

  return (
    <div className="container mx-auto py-8 px-4 md:px-0">
      <Button variant="ghost" onClick={() => router.back()} className="mb-6">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Geri Dön
      </Button>

      {isOwner && (
        <div className="flex gap-2 mb-6">
          <Button onClick={() => router.push(`/jobs/${jobId}/applications`)} variant="default">
            <Users className="mr-2 h-4 w-4" />
            Başvuruları Gör
          </Button>
          <Button onClick={() => router.push(`/jobs/${jobId}/edit`)} variant="outline">
            <Edit className="mr-2 h-4 w-4" />
            Düzenle
          </Button>
          <Button onClick={handleDelete} variant="destructive">
            <Trash2 className="mr-2 h-4 w-4" />
            Sil
          </Button>
        </div>
      )}

      <div className="grid gap-8 md:grid-cols-3">
        <div className="md:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">{job.title}</CardTitle>
              <CardDescription className="text-lg font-medium flex items-center">
                <Building className="mr-2 h-5 w-5" />
                {job.company_name}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center text-sm">
                  <MapPin className="mr-2 h-4 w-4" />
                  {job.location}
                </div>
                <div className="flex items-center text-sm">
                  <Briefcase className="mr-2 h-4 w-4" />
                  {job.work_type} • {job.job_type}
                </div>
                <div className="flex items-center text-sm">
                  <Users className="mr-2 h-4 w-4" />
                  {job.experience_level}
                </div>
                <div className="flex items-center text-sm">
                  <Clock className="mr-2 h-4 w-4" />
                  {job.sector}
                </div>
              </div>
              
              {(job.salary_min || job.salary_max) && (
                <div className="flex items-center text-lg font-semibold text-green-600">
                  <DollarSign className="mr-2 h-5 w-5" />
                  {job.salary_min && job.salary_max 
                    ? `${job.salary_min.toLocaleString()} - ${job.salary_max.toLocaleString()} TL`
                    : job.salary_min 
                    ? `${job.salary_min.toLocaleString()}+ TL`
                    : `${job.salary_max?.toLocaleString()} TL'ye kadar`
                  }
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>İş Tanımı</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="leading-relaxed">{job.description}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Aranan Nitelikler</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {requirementsList.map((requirement, index) => (
                  <li key={index} className="flex items-start">
                    <CheckCircle className="mr-2 h-4 w-4 text-green-500 mt-0.5" />
                    <span className="text-sm">{requirement}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Gerekli Beceriler</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {skillsList.map((skill, index) => (
                  <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                    {skill}
                  </span>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          {userRole === "aday" && (
            <Card>
              <CardHeader>
                <CardTitle>Başvuru</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button 
                  className="w-full" 
                  size="lg"
                  onClick={handleApply}
                  disabled={hasApplied || isApplying}
                >
                  {hasApplied ? "Başvurdunuz" : isApplying ? "Başvuruluyor..." : "Başvur"}
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full"
                  onClick={handleToggleFavorite}
                >
                  {isFavorite ? "Favorilerden Çıkar" : "Favorilere Ekle"}
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
