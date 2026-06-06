"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft, CheckCircle, XCircle, AlertCircle, Loader2 } from "lucide-react";
import { getDetailedMatch, type DetailedMatchResponse } from "@/lib/api";

function ScoreGauge({ score, label }: { score: number; label: string }) {
  const getColor = () => {
    if (label === "Düşük Uyum") return "text-red-600";
    if (label === "Potansiyel Uyum") return "text-yellow-600";
    if (label === "Orta Uyum") return "text-blue-600";
    return "text-green-600";
  };
  
  const getBg = () => {
    if (label === "Düşük Uyum") return "bg-red-50 border-red-200";
    if (label === "Potansiyel Uyum") return "bg-yellow-50 border-yellow-200";
    if (label === "Orta Uyum") return "bg-blue-50 border-blue-200";
    return "bg-green-50 border-green-200";
  };
  
  return (
    <div className={`flex flex-col items-center justify-center p-8 rounded-2xl border-2 ${getBg()}`}>
      <span className={`text-7xl font-black ${getColor()}`}>%{Math.round(score)}</span>
      <span className={`text-sm font-semibold mt-2 ${getColor()}`}>
        {label}
      </span>
    </div>
  );
}

function ScoreBar({ label, score, max = 25 }: { label: string; score: number; max?: number }) {
  const isPenalty = score < 0;
  const pct = isPenalty ? 100 : Math.max(0, Math.min((score / max) * 100, 100));
  const color = isPenalty ? "bg-red-600" : (pct >= 70 ? "bg-green-500" : pct >= 40 ? "bg-yellow-500" : "bg-red-500");
  
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className={isPenalty ? "text-red-600 font-bold" : "text-muted-foreground"}>
          {isPenalty ? Math.round(score) : `${Math.round(score)} / ${max}`}
        </span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function DetailedMatchPage({
  params,
}: {
  params: Promise<{ id: string; resumeId: string }>;
}) {
  const router = useRouter();
  const [data, setData] = useState<DetailedMatchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ids, setIds] = useState<{ jobId: string; resumeId: string } | null>(null);

  useEffect(() => {
    params.then((p) => setIds({ jobId: p.id, resumeId: p.resumeId }));
  }, [params]);

  useEffect(() => {
    if (!ids) return;
    const token = localStorage.getItem("accessToken");
    if (!token) { router.push("/login"); return; }

    getDetailedMatch(token, Number(ids.jobId), Number(ids.resumeId))
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setIsLoading(false));
  }, [ids, router]);

  if (isLoading) {
    return (
      <div className="container mx-auto py-16 text-center">
        <Loader2 className="h-10 w-10 animate-spin mx-auto mb-4" />
        <p className="text-muted-foreground">Detaylı analiz hazırlanıyor...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container mx-auto py-8">
        <Button variant="ghost" onClick={() => router.back()} className="mb-4">
          <ArrowLeft className="mr-2 h-4 w-4" /> Geri Dön
        </Button>
        <Card>
          <CardContent className="py-12 text-center text-destructive">
            {error || "Veri yüklenemedi."}
          </CardContent>
        </Card>
      </div>
    );
  }

  const { job, candidate, analysis } = data;

  return (
    <div className="container mx-auto py-8 px-4 md:px-0 max-w-4xl space-y-6">
      <Button variant="ghost" onClick={() => router.back()}>
        <ArrowLeft className="mr-2 h-4 w-4" /> Geri Dön
      </Button>

      {/* Başlık */}
      <div>
        <h1 className="text-3xl font-bold">{candidate.full_name}</h1>
        <p className="text-muted-foreground mt-1">
          {job.title} — {job.company_name}
        </p>
      </div>

      {/* Genel Skor + Döküm */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="flex flex-col gap-4">
          <ScoreGauge score={analysis.overall_score} label={analysis.score_label} />
          <div className="text-center text-sm text-muted-foreground bg-slate-50 p-4 rounded-xl border">
            <p className="font-semibold text-foreground mb-2">Skor Özeti</p>
            <p className="text-left">{analysis.summary_text}</p>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Skor Dökümü</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ScoreBar label="Anlamsal Benzerlik" score={analysis.base_similarity * 0.4} max={40} />
            <ScoreBar label="Beceri Uyumu (Bonus)" score={analysis.skill_analysis.score} max={25} />
            <ScoreBar label="Eğitim Uyumu" score={analysis.education_analysis.score} max={25} />
            <ScoreBar label="Deneyim Uyumu" score={analysis.experience_analysis.score} max={25} />
            {analysis.critical_analysis.score !== 0 && (
              <ScoreBar 
                label={analysis.critical_analysis.score < 0 ? "Kritik Eksiklik Cezası" : "Kritik Beceri Bonusu"} 
                score={analysis.critical_analysis.score < 0 ? analysis.critical_analysis.score : analysis.critical_analysis.score * 0.1} 
                max={analysis.critical_analysis.score < 0 ? 0 : 10} 
              />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Beceri Karşılaştırması */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Beceri Karşılaştırması
            <span className={`ml-2 text-sm font-normal ${
              analysis.skill_analysis.match_percentage === 0 ? 'text-red-600 font-semibold' :
              analysis.skill_analysis.match_percentage < 30 ? 'text-orange-600' :
              'text-muted-foreground'
            }`}>
              %{Math.round(analysis.skill_analysis.match_percentage)} eşleşme
              {analysis.skill_analysis.match_percentage === 0 && " - KRİTİK!"}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm font-semibold text-green-700 mb-2 flex items-center gap-1">
              <CheckCircle className="h-4 w-4" /> Eşleşen Beceriler
            </p>
            {analysis.skill_analysis.matched_skills.length === 0 ? (
              <p className="text-sm text-muted-foreground">Eşleşen beceri yok</p>
            ) : (
              <div className="flex flex-wrap gap-1">
                {analysis.skill_analysis.matched_skills.map((s) => (
                  <span key={s} className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">
                    {s}
                  </span>
                ))}
              </div>
            )}
          </div>
          <div>
            <p className="text-sm font-semibold text-red-700 mb-2 flex items-center gap-1">
              <XCircle className="h-4 w-4" /> Eksik Beceriler
            </p>
            {analysis.skill_analysis.missing_skills.length === 0 ? (
              <p className="text-sm text-muted-foreground">Eksik beceri yok</p>
            ) : (
              <div className="flex flex-wrap gap-1">
                {analysis.skill_analysis.missing_skills.map((s) => (
                  <span key={s} className="text-xs px-2 py-1 bg-red-100 text-red-800 rounded-full">
                    {s}
                  </span>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Deneyim Karşılaştırması */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Deneyim Karşılaştırması</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="text-center p-4 bg-muted rounded-lg">
              <p className="text-3xl font-bold">{analysis.experience_analysis.candidate_years}</p>
              <p className="text-sm text-muted-foreground mt-1">Adayın Deneyimi (yıl)</p>
            </div>
            <div className="text-center p-4 bg-muted rounded-lg">
              <p className="text-3xl font-bold">{analysis.experience_analysis.required_years}</p>
              <p className="text-sm text-muted-foreground mt-1">Gereken Deneyim (yıl)</p>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">{analysis.experience_analysis.message}</p>
        </CardContent>
      </Card>

      {/* Eğitim Durumu */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Eğitim Uyumu</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-start gap-3">
            {analysis.education_analysis.status === "excellent" ? (
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 shrink-0" />
            ) : analysis.education_analysis.status === "poor" ? (
              <XCircle className="h-5 w-5 text-red-600 mt-0.5 shrink-0" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 shrink-0" />
            )}
            <p className="text-sm">{analysis.education_analysis.message}</p>
          </div>
        </CardContent>
      </Card>

      {/* Öneriler */}
      {analysis.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Değerlendirme Notları</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {analysis.recommendations.map((rec, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5 shrink-0" />
                  {rec}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Aksiyon */}
      <div className="flex gap-3 pb-8">
        <Button onClick={() => window.location.href = `mailto:${candidate.email}`} className="flex-1">
          Mülakata Davet Et
        </Button>
        <Button variant="outline" onClick={() => router.back()}>
          Listeye Dön
        </Button>
      </div>
    </div>
  );
}
