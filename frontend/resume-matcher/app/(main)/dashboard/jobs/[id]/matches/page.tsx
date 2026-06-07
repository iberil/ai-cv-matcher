"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, Mail, Briefcase, GraduationCap, Loader2, Star } from "lucide-react";
import MessagesDrawer from "@/components/MessagesDrawer";
import { sendMessage } from "@/lib/api";

interface Candidate {
  id: number;
  user_id: number;
  full_name: string;
  email: string;
  match_score: number;
  skills: string;
  experience_years: number;
  education: string;
  created_at: string;
}

export default function MatchesPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const [jobId, setJobId] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [jobTitle, setJobTitle] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, matched: 0, processingTime: 0 });
  
  // Messaging States
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [targetUser, setTargetUser] = useState<{ id: number; name: string } | null>(null);
  const [initialMessage, setInitialMessage] = useState("");

  const handleContact = async (candidate: Candidate) => {
    try {
      const token = localStorage.getItem("accessToken");
      if (!token) {
        router.push("/login");
        return;
      }

      const msgContent = `Merhaba ${candidate.full_name}, yayınladığımız ${jobTitle} pozisyonu için profiliniz oldukça uygun görünüyor. Sizinle detayları konuşmak üzere iletişime geçmek isteriz.`;
      
      // Mesajı otomatik gönder
      await sendMessage(token, candidate.user_id, msgContent, jobId ? parseInt(jobId) : undefined);
      
      // Drawer'ı aç
      setTargetUser({ id: candidate.user_id, name: candidate.full_name });
      setInitialMessage(""); // Başarıyla gönderildiği için input boş olabilir veya son mesajı gösterebilir
      setIsDrawerOpen(true);
    } catch (error) {
      console.error("Mesaj gönderilemedi:", error);
      alert("İletişim başlatılamadı.");
    }
  };

  useEffect(() => {
    const getParams = async () => {
      const resolvedParams = await params;
      setJobId(resolvedParams.id);
    };
    getParams();
  }, [params]);

  useEffect(() => {
    if (!jobId) return;

    const fetchCandidates = async () => {
      try {
        const token = localStorage.getItem("accessToken");
        if (!token) {
          router.push("/login");
          return;
        }

        // İş ilanı bilgisini al
        const jobResponse = await fetch(`http:///api/v1/jobs/${jobId}`);
        if (jobResponse.ok) {
          const jobData = await jobResponse.json();
          setJobTitle(jobData.title);
        }

        // Adayları al
        const response = await fetch(
          `http:///api/v1/jobs/${jobId}/matches?limit=50`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );

        if (response.ok) {
          const data = await response.json();
          setCandidates(data.candidates);
          setStats({
            total: data.total_candidates,
            matched: data.matched_candidates,
            processingTime: data.processing_time
          });
        }
      } catch (error) {
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCandidates();
  }, [jobId, router]);

  const getScoreColor = (score: number) => {
    if (score >= 70) return "text-green-600 bg-green-50";
    if (score >= 50) return "text-yellow-600 bg-yellow-50";
    return "text-red-600 bg-red-50";
  };

  const getScoreLabel = (score: number) => {
    if (score >= 70) return "Yüksek Uyum";
    if (score >= 50) return "Orta Uyum";
    return "Düşük Uyum";
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto" />
        <p className="mt-4">Adaylar analiz ediliyor...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 md:px-0 relative">
      <Button variant="ghost" onClick={() => router.back()} className="mb-6">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Geri Dön
      </Button>

      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">{jobTitle}</h1>
        <p className="text-muted-foreground">
          {candidates.length} uygun aday bulundu • İşlem süresi: {stats.processingTime}s
        </p>
      </div>

      {candidates.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">Henüz bu ilana uygun aday bulunamadı</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {candidates.map((candidate) => (
            <Card key={candidate.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-xl">{candidate.full_name}</CardTitle>
                    <CardDescription className="flex items-center mt-1">
                      <Mail className="h-4 w-4 mr-1" />
                      {candidate.email}
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-500 mb-1">Uyum Skoru</div>
                    <div className={`text-3xl font-bold ${getScoreColor(candidate.match_score).split(' ')[0]}`}>
                      %{candidate.match_score}
                    </div>
                    <div className={`text-xs px-2 py-1 rounded mt-1 ${getScoreColor(candidate.match_score)}`}>
                      {getScoreLabel(candidate.match_score)}
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-start">
                  <Briefcase className="h-4 w-4 mr-2 mt-1 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">Deneyim</p>
                    <p className="text-sm text-muted-foreground">
                      {candidate.experience_years} yıl deneyim
                    </p>
                  </div>
                </div>

                <div className="flex items-start">
                  <GraduationCap className="h-4 w-4 mr-2 mt-1 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">Eğitim</p>
                    <p className="text-sm text-muted-foreground">{candidate.education}</p>
                  </div>
                </div>

                <div className="flex items-start">
                  <Star className="h-4 w-4 mr-2 mt-1 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">Beceriler</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {candidate.skills.split(',').slice(0, 5).map((skill, idx) => (
                        <span key={idx} className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded">
                          {skill.trim()}
                        </span>
                      ))}
                      {candidate.skills.split(',').length > 5 && (
                        <span className="text-xs px-2 py-1 bg-gray-50 text-gray-700 rounded">
                          +{candidate.skills.split(',').length - 5} daha
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button 
                    className="flex-1" 
                    onClick={() => router.push(`/dashboard/jobs/${jobId}/matches/${candidate.id}`)}
                  >
                    Detaylı Rapor
                  </Button>
                  <Button variant="outline" className="flex-1" onClick={() => handleContact(candidate)}>
                    <Mail className="mr-2 h-4 w-4" />
                    İletişime Geç
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Messages Drawer */}
      <MessagesDrawer 
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        targetUserId={targetUser?.id}
        targetUserName={targetUser?.name}
        initialMessage={initialMessage}
        targetJobId={jobId ? parseInt(jobId) : null}
      />
    </div>
  );
}
