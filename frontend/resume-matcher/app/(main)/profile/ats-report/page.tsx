"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  CardDescription 
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  Tooltip as RechartsTooltip,
  Label as RechartsLabel 
} from "recharts";
import { 
  ChevronLeft, 
  AlertCircle, 
  CheckCircle2, 
  Info, 
  Sparkles, 
  Loader2,
  FileText,
  Target,
  Layout,
  Zap
} from "lucide-react";
import { analyzeATS, getCareerAdvice, ATSScoreResponse } from "@/lib/api";

function ATSReportContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const cvId = searchParams.get("cvId");
  
  const [report, setReport] = useState<ATSScoreResponse | null>(null);
  const [chatMessages, setChatMessages] = useState<{role: string, content: string}[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isAdviceLoading, setIsAdviceLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!cvId) {
      setError("CV ID bulunamadı.");
      setIsLoading(false);
      return;
    }

    const fetchReport = async () => {
      const token = localStorage.getItem("accessToken");
      if (!token) {
        router.push("/login");
        return;
      }

      try {
        const data = await analyzeATS(token, parseInt(cvId));
        setReport(data);
      } catch (err: any) {
        setError(err.message || "ATS analizi alınırken bir hata oluştu.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchReport();
  }, [cvId, router]);

  const handleSendMessage = async (initialMessage?: string) => {
    if (!cvId) return;
    
    const content = initialMessage || chatInput;
    if (!content.trim()) return;

    const newMessages = [...chatMessages, { role: "user", content }];
    setChatMessages(newMessages);
    setChatInput("");
    setIsAdviceLoading(true);
    
    try {
      const token = localStorage.getItem("accessToken");
      const { sendCareerChatMessage } = await import("@/lib/api");
      const data = await sendCareerChatMessage(token!, parseInt(cvId), newMessages);
      
      setChatMessages((prev) => [...prev, { role: "assistant", content: data.advice }]);
    } catch (err) {
      console.error(err);
      setChatMessages((prev) => [...prev, { role: "assistant", content: "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin." }]);
    } finally {
      setIsAdviceLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
        <p className="text-gray-600 font-medium animate-pulse">ATS Optimizasyon Analizi Yapılıyor...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="container mx-auto py-12 px-4 max-w-2xl text-center">
        <div className="bg-red-50 p-8 rounded-2xl border border-red-100">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-red-900 mb-2">Hata Oluştu</h2>
          <p className="text-red-700 mb-6">{error || "Rapor yüklenemedi."}</p>
          <Button onClick={() => router.back()} variant="outline">Geri Dön</Button>
        </div>
      </div>
    );
  }

  // Gauge Chart Data
  const chartData = [
    { name: "Score", value: report.overall_score },
    { name: "Remaining", value: 100 - report.overall_score }
  ];

  const getScoreColor = (score: number) => {
    if (score >= 85) return "#10b981"; // Green (Mükemmel)
    if (score >= 70) return "#3b82f6"; // Blue (İyi)
    if (score >= 50) return "#f59e0b"; // Yellow (Orta)
    if (score >= 35) return "#f97316"; // Orange (Gelişime Açık)
    return "#ef4444"; // Red (Yetersiz)
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        <div className="mb-8">
          <Button 
            variant="ghost" 
            onClick={() => router.back()}
            className="-ml-4 mb-4 flex items-center gap-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100/50"
          >
            <ChevronLeft className="h-4 w-4" />
            Profile Dön
          </Button>
          <h1 className="text-3xl font-bold text-gray-900">ATS Analiz Raporu</h1>
          <p className="text-gray-600 mt-1">CV'nizin sistemlere uyumluluğunu detaylı olarak inceleyin</p>
        </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Sol Panel: Skor ve Özet */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="overflow-hidden border-none shadow-xl bg-white/80 backdrop-blur-md">
            <CardHeader className="text-center pb-2">
              <CardTitle className="text-xl">Genel ATS Skoru</CardTitle>
              <CardDescription>CV'nizin makine okunabilirliği</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64 w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={chartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={70}
                      outerRadius={90}
                      startAngle={180}
                      endAngle={0}
                      paddingAngle={0}
                      dataKey="value"
                    >
                      <Cell fill={getScoreColor(report.overall_score)} />
                      <Cell fill="#f1f5f9" />
                      <RechartsLabel 
                        value={`${report.overall_score}%`} 
                        position="center" 
                        className="text-4xl font-bold fill-gray-900" 
                      />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute bottom-12 left-0 right-0 text-center">
                   <span className={`px-4 py-1 rounded-full text-sm font-bold text-white shadow-sm`} style={{ backgroundColor: getScoreColor(report.overall_score) }}>
                    {report.compliance_level}
                  </span>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mt-6">
                <div className="bg-slate-50 p-3 rounded-xl text-center border border-slate-100">
                  <p className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1">Layout</p>
                  <p className="text-lg font-bold text-slate-900">{report.layout_score}%</p>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl text-center border border-slate-100">
                  <p className="text-xs text-slate-500 uppercase font-bold tracking-wider mb-1">İçerik</p>
                  <p className="text-lg font-bold text-slate-900">{report.content_score}%</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-none shadow-xl bg-white/80 backdrop-blur-md">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center">
                  <Zap className="h-5 w-5 text-amber-500 fill-amber-500" />
                </div>
                <h3 className="font-bold text-lg text-slate-900">Hızlı İstatistik</h3>
              </div>
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                  <span className="text-slate-600 font-medium">Eylem Fiilleri</span>
                  <span className="font-bold text-xl text-slate-900">{report.action_verb_count}</span>
                </div>
                <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                  <span className="text-slate-600 font-medium">Okunabilirlik</span>
                  <span className="font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full text-sm">Yüksek</span>
                </div>
                <p className="text-sm text-slate-500 italic mt-2">
                  Eylem fiilleri CV'nizi daha etkileyici ve sonuç odaklı gösterir.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sağ Panel: Analiz Detayları ve Geri Bildirim */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-none shadow-xl">
             <CardHeader className="border-b bg-slate-50/50">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl">Kapsamlı Analiz Raporu</CardTitle>
                  <CardDescription>Saptanan sorunlar ve başarılar</CardDescription>
                </div>
                <Target className="h-8 w-8 text-blue-500 opacity-20" />
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                {report.feedback.map((item, idx) => (
                  <div 
                    key={idx} 
                    className={`flex items-start gap-4 p-4 rounded-xl border transition-all hover:shadow-md ${
                      item.type === 'critical' || item.type === 'error' ? 'bg-red-50 border-red-100' :
                      item.type === 'warning' ? 'bg-amber-50 border-amber-100' :
                      'bg-emerald-50 border-emerald-100'
                    }`}
                  >
                    <div className="mt-1">
                      {item.type === 'critical' || item.type === 'error' ? <AlertCircle className="h-5 w-5 text-red-600" /> :
                       item.type === 'warning' ? <Info className="h-5 w-5 text-amber-600" /> :
                       <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                      }
                    </div>
                    <div>
                      <p className={`font-bold text-sm uppercase tracking-tighter mb-0.5 ${
                        item.type === 'critical' || item.type === 'error' ? 'text-red-700' :
                        item.type === 'warning' || item.type === 'info' ? 'text-amber-700' :
                        'text-emerald-700'
                      }`}>
                        {item.type === 'critical' ? 'Kritik Sorun' : 
                         item.type === 'error' ? 'Hata' :
                         item.type === 'warning' ? 'Uyarı' : 
                         item.type === 'info' ? 'Bilgi' : 'Başarılı'}
                      </p>
                      <p className="text-slate-700 leading-snug">{item.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Kariyer Danışmanı Bölümü */}
          <Card className="border-none shadow-2xl bg-white relative overflow-hidden flex flex-col h-[500px]">
            <div className="absolute top-0 left-0 w-1 h-full bg-blue-600" />
            <CardHeader className="border-b bg-slate-50/50 pb-4">
               <div className="flex items-center gap-4">
                 <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center shrink-0 shadow-inner">
                   <Sparkles className="h-6 w-6 text-blue-600" />
                 </div>
                 <div>
                   <CardTitle className="text-xl">AI Kariyer Danışmanı</CardTitle>
                   <CardDescription>CV'nizi geliştirmek için tavsiyeler alın veya soru sorun.</CardDescription>
                 </div>
               </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50/30">
              {chatMessages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
                  <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center shadow-inner">
                    <Sparkles className="h-10 w-10 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-900 mb-2">CV'nizi Nasıl Geliştirebiliriz?</h3>
                    <p className="text-slate-600 max-w-md mx-auto">
                      Skorunuzu artırmak ve mülakata çağrılma şansınızı yükseltmek için kişiselleştirilmiş tavsiyeler alın.
                    </p>
                  </div>
                  <Button 
                    onClick={() => handleSendMessage("CV'mi geliştirmek için bana genel bir değerlendirme ve tavsiyeler verebilir misin?")} 
                    disabled={isAdviceLoading}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-6 px-8 rounded-2xl shadow-xl hover:scale-105 transition-all group"
                  >
                    {isAdviceLoading ? (
                      <>
                        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                        Analiz Ediliyor...
                      </>
                    ) : (
                      <>
                        Analizi Başlat
                        <ChevronLeft className="ml-2 h-5 w-5 rotate-180 group-hover:translate-x-1 transition-transform" />
                      </>
                    )}
                  </Button>
                </div>
              ) : (
                chatMessages.map((msg, idx) => (
                  <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] p-4 rounded-2xl ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-none shadow-md' : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none shadow-sm'}`}>
                      {msg.role === 'assistant' && (
                        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-slate-100">
                          <Sparkles className="h-4 w-4 text-blue-500" />
                          <span className="font-bold text-xs text-blue-600 uppercase tracking-wider">AI Danışman</span>
                        </div>
                      )}
                      <div className="whitespace-pre-wrap leading-relaxed">
                        {msg.content}
                      </div>
                    </div>
                  </div>
                ))
              )}
              {isAdviceLoading && chatMessages.length > 0 && (
                <div className="flex justify-start">
                   <div className="bg-white border border-slate-200 p-4 rounded-2xl rounded-bl-none shadow-sm flex items-center gap-3">
                     <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                     <span className="text-sm text-slate-500 font-medium">Danışman yazıyor...</span>
                   </div>
                </div>
              )}
            </CardContent>
            {chatMessages.length > 0 && (
              <div className="p-4 bg-white border-t">
                <form 
                  onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
                  className="flex gap-2"
                >
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Tavsiye hakkında bir soru sorun..."
                    className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                    disabled={isAdviceLoading}
                  />
                  <Button 
                    type="submit" 
                    disabled={isAdviceLoading || !chatInput.trim()}
                    className="bg-blue-600 hover:bg-blue-700 text-white h-auto px-6 rounded-xl shadow-md"
                  >
                    Gönder
                  </Button>
                </form>
              </div>
            )}
          </Card>
        </div>
      </div>

      <div className="mt-12 text-center text-slate-400 text-sm">
        Analiz Tarihi: {new Date(report.analyzed_at).toLocaleString('tr-TR')} • Qwen-72B Career Insight Engine
      </div>
      </div>
    </div>
  );
}

export default function ATSReportPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><Loader2 className="animate-spin" /></div>}>
      <ATSReportContent />
    </Suspense>
  );
}
