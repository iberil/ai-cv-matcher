"use client";

import { useState, useEffect } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Briefcase, MapPin, Sparkles, Filter, X, Clock, DollarSign, Loader2 } from "lucide-react";
import { getJobPostings, matchJobsWithCV, type JobPostingWithScore } from "@/lib/api";
import { getCurrentUser } from "@/lib/api";
import { matchCache, clearMatchCache } from "@/lib/match-cache";

const experienceLevels = [
  { value: "all", label: "Tümü" },
  { value: "entry", label: "Giriş Seviyesi (0-2 yıl)" },
  { value: "mid", label: "Orta Seviye (3-5 yıl)" },
  { value: "senior", label: "Kıdemli (6-10 yıl)" },
  { value: "lead", label: "Lider (10+ yıl)" },
];

const jobTypes = [
  { value: "all", label: "Tümü" },
  { value: "full-time", label: "Tam Zamanlı" },
  { value: "part-time", label: "Yarı Zamanlı" },
  { value: "contract", label: "Sözleşmeli" },
  { value: "internship", label: "Staj" },
];

const workTypes = [
  { value: "all", label: "Tümü" },
  { value: "office", label: "Ofiste" },
  { value: "remote", label: "Uzaktan" },
  { value: "hybrid", label: "Hibrit" },
];

const locations = [
  { value: "all", label: "Tümü" },
  { value: "istanbul", label: "İstanbul" },
  { value: "ankara", label: "Ankara" },
  { value: "izmir", label: "İzmir" },
  { value: "bursa", label: "Bursa" },
  { value: "antalya", label: "Antalya" },
  { value: "adana", label: "Adana" },
  { value: "gaziantep", label: "Gaziantep" },
  { value: "kayseri", label: "Kayseri" },
  { value: "kocaeli", label: "Kocaeli" },
  { value: "uzaktan", label: "Uzaktan" },
];

const sectors = [
  { value: "all", label: "Tümü" },
  { value: "teknoloji", label: "Teknoloji" },
  { value: "yazılım", label: "Yazılım" },
  { value: "bilişim", label: "Bilişim" },
  { value: "finans", label: "Finans" },
  { value: "bankacılık", label: "Bankacılık" },
  { value: "sağlık", label: "Sağlık ve İlaç" },
  { value: "eğitim", label: "Eğitim ve Danışmanlık" },
  { value: "üretim", label: "Üretim" },
  { value: "e-ticaret", label: "E-Ticaret" },
  { value: "enerji", label: "Enerji" },
  { value: "savunma", label: "Savunma" },
  { value: "telekom", label: "Telekom" },
  { value: "pazarlama", label: "Pazarlama" },
  { value: "lojistik", label: "Lojistik ve Taşımacılık" },
  { value: "tarım", label: "Tarım ve Hayvancılık" },
  { value: "gıda", label: "Gıda ve Restoran" },
  { value: "inşaat", label: "İnşaat ve Emlak" },
  { value: "tekstil", label: "Tekstil ve Moda" },
  { value: "hukuk", label: "Hukuk ve Uyum" },
  { value: "medya", label: "Medya ve Sanat" },
  { value: "turizm", label: "Turizm ve Otelcilik" },
];

export default function JobSearchPage() {
  const router = useRouter();
  const [jobs, setJobs] = useState<JobPostingWithScore[]>([]);
  const [originalJobs, setOriginalJobs] = useState<JobPostingWithScore[]>([]);
  const [aiFilterApplied, setAiFilterApplied] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isMatching, setIsMatching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [userCVId, setUserCVId] = useState<number | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);

  const [filters, setFilters] = useState({
    position: "",
    location: "",
    experienceLevel: "",
    jobType: "",
    workType: "",
    sector: "",
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);

        const jobsData = await getJobPostings(0, 2000);
        const jobsWithScore = jobsData.map(job => ({ ...job, match_score: 0 }));
        
        setOriginalJobs(jobsWithScore);

        const token = localStorage.getItem("accessToken");
        if (token) {
          const user = await getCurrentUser(token);
          setUserRole(user.user_role);
          setUserCVId(1); // CV ID placeholder

          // Global Önbellek (Singleton) kontrolü
          // Sadece aynı kullanıcı ise ve veri varsa kullan
          if (matchCache.userId === user.id && matchCache.results) {
            console.log("DEBUG: Önbellekteki eşleşme sonuçları yükleniyor...");
            setJobs(matchCache.results);
            setAiFilterApplied(true);
          } else {
            setJobs(jobsWithScore);
            setAiFilterApplied(false);
          }
        } else {
          setJobs(jobsWithScore);
          setAiFilterApplied(false);
          clearMatchCache();
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  const handleAiSearch = async () => {
    if (!userCVId) {
      alert("CV bulunamadı. Lütfen önce CV yükleyin.");
      return;
    }

    const token = localStorage.getItem("accessToken");
    if (!token) {
      alert("Lütfen giriş yapın.");
      return;
    }

    try {
      setIsMatching(true);
      const matchResult = await matchJobsWithCV(token, userCVId, 20);

      setJobs(matchResult.matches);
      setAiFilterApplied(true);

      // Sonuçları Global Önbelleğe (Singleton) kaydet - F5 ile silinir
      if (token) {
        const user = await getCurrentUser(token);
        matchCache.userId = user.id;
        matchCache.results = matchResult.matches;
      }

      alert(`${matchResult.matches.length} iş ilanı CV'nize göre sıralandı! (İşlem süresi: ${matchResult.processing_time}s)`);
    } catch (err: any) {
      setError(err.message);
      alert("Eşleştirme sırasında hata oluştu: " + err.message);
    } finally {
      setIsMatching(false);
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    let filteredJobs = originalJobs;

    if (filters.position) {
      filteredJobs = filteredJobs.filter(job =>
        job.title.toLowerCase().includes(filters.position.toLowerCase())
      );
    }

    if (filters.location && filters.location !== "all") {
      filteredJobs = filteredJobs.filter(job =>
        job.location?.toLowerCase().includes(filters.location.toLowerCase())
      );
    }

    if (filters.experienceLevel && filters.experienceLevel !== "all") {
      filteredJobs = filteredJobs.filter(job =>
        job.experience_level === filters.experienceLevel
      );
    }

    if (filters.jobType && filters.jobType !== "all") {
      filteredJobs = filteredJobs.filter(job =>
        job.job_type === filters.jobType
      );
    }

    if (filters.workType && filters.workType !== "all") {
      filteredJobs = filteredJobs.filter(job =>
        job.work_type === filters.workType
      );
    }

    if (filters.sector && filters.sector !== "all") {
      filteredJobs = filteredJobs.filter((job) =>
        job.sector?.toLowerCase().includes(filters.sector.toLowerCase())
      );
    }

    setJobs(filteredJobs);
    setAiFilterApplied(false);
  };

  const clearFilters = () => {
    setFilters({
      position: "",
      location: "",
      experienceLevel: "",
      jobType: "",
      workType: "",
      sector: "",
    });
    setJobs(originalJobs);
    setAiFilterApplied(false);
    
    // Global Önbelleği temizle
    clearMatchCache();
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4 md:px-0 text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
        <p>İş ilanları yükleniyor...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 px-4 md:px-0 text-center">
        <p className="text-red-500">Hata: {error}</p>
        <Button onClick={() => window.location.reload()} className="mt-4">
          Tekrar Dene
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 md:px-0">
      <header className="mb-8">
        <h1 className="text-4xl font-bold tracking-tight">
          İş İlanlarını Keşfet
        </h1>
        <p className="text-muted-foreground mt-2">
          Kariyerinizdeki bir sonraki adımı burada bulun.
        </p>
      </header>

      <div className="mb-6">
        <Button
          onClick={() => setShowFilters(!showFilters)}
          variant="outline"
          className="mb-4"
        >
          <Filter className="mr-2 h-4 w-4" />
          {showFilters ? "Filtreleri Gizle" : "Filtreleri Göster"}
        </Button>
      </div>

      {showFilters && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Filtreleme Seçenekleri</CardTitle>
            <CardDescription>
              İş ilanlarını ihtiyaçlarınıza göre filtreleyin
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="position">Pozisyon</Label>
                <Input
                  id="position"
                  placeholder="örn: Yazılım Mühendisi"
                  value={filters.position}
                  onChange={(e) => handleFilterChange("position", e.target.value)}
                />
              </div>

              <div className="grid gap-2">
                <Label>Konum</Label>
                <Select value={filters.location} onValueChange={(value) => handleFilterChange("location", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Şehir seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {locations.map((location) => (
                      <SelectItem key={location.value} value={location.value}>
                        {location.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label>Deneyim Düzeyi</Label>
                <Select value={filters.experienceLevel} onValueChange={(value) => handleFilterChange("experienceLevel", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Deneyim düzeyi seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {experienceLevels.map((level) => (
                      <SelectItem key={level.value} value={level.value}>
                        {level.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label>İş Türü</Label>
                <Select value={filters.jobType} onValueChange={(value) => handleFilterChange("jobType", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="İş türü seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {jobTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label>Çalışma Türü</Label>
                <Select value={filters.workType} onValueChange={(value) => handleFilterChange("workType", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Çalışma türü seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {workTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label>Sektör</Label>
                <Select value={filters.sector} onValueChange={(value) => handleFilterChange("sector", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Sektör seçin" />
                  </SelectTrigger>
                  <SelectContent>
                    {sectors.map((sector) => (
                      <SelectItem key={sector.value} value={sector.value}>
                        {sector.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex gap-2">
            <Button onClick={applyFilters}>Filtreleri Uygula</Button>
            <Button variant="outline" onClick={clearFilters}>
              <X className="mr-2 h-4 w-4" />
              Temizle
            </Button>
          </CardFooter>
        </Card>
      )}

      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold">{jobs.length} İlan Bulundu</h2>
        {userRole === "aday" && (
          <Button
            onClick={handleAiSearch}
            variant="outline"
            disabled={isMatching || !userCVId}
          >
            {isMatching && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {isMatching ? "Eşleştiriliyor..." : "CV ile Uyumluluğa Göre Sırala"}
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {jobs.map((job) => (
          <Card key={job.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              {aiFilterApplied && job.match_score > 0 && (
                <div className="text-sm font-bold text-green-600 mb-2">
                  %{job.match_score.toFixed(1)} Uyumlu
                </div>
              )}
              <CardTitle className="text-lg">{job.title}</CardTitle>
              <CardDescription className="font-medium">{job.company_name}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {job.location && (
                <div className="flex items-center text-sm text-muted-foreground">
                  <MapPin className="mr-2 h-4 w-4" />
                  {job.location}
                </div>
              )}
              <div className="flex items-center text-sm text-muted-foreground">
                <Briefcase className="mr-2 h-4 w-4" />
                {job.work_type} • {job.job_type}
              </div>
              {job.experience_level && (
                <div className="flex items-center text-sm text-muted-foreground">
                  <Clock className="mr-2 h-4 w-4" />
                  {job.experience_level}
                </div>
              )}
              {(job.salary_min || job.salary_max) && (
                <div className="flex items-center text-sm text-muted-foreground">
                  <DollarSign className="mr-2 h-4 w-4" />
                  {job.salary_min && job.salary_max
                    ? `${job.salary_min} - ${job.salary_max} TL`
                    : job.salary_min
                      ? `${job.salary_min}+ TL`
                      : `${job.salary_max} TL'ye kadar`
                  }
                </div>
              )}
              {job.sector && (
                <div className="text-sm text-blue-600 font-medium">
                  {job.sector}
                </div>
              )}
            </CardContent>
            <CardFooter>
              <Button
                className="w-full"
                variant="secondary"
                onClick={() => {
                  console.log('Job ID:', job.id);
                  router.push(`/jobs/${job.id}`);
                }}
              >
                Detayları Gör
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {jobs.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Henüz iş ilanı bulunmuyor.</p>
        </div>
      )}
    </div>
  );
}