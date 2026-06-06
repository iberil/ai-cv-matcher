'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getCompetitorAnalysis, CompetitorAnalysisResponse } from '@/lib/api';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

export default function JobAnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  
  const [analysis, setAnalysis] = useState<CompetitorAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const token = localStorage.getItem('accessToken');
        if (!token) {
          router.push('/login');
          return;
        }
        
        const data = await getCompetitorAnalysis(jobId, token);
        setAnalysis(data);
      } catch (err: any) {
        setError(err.message || 'Analiz yüklenemedi');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [jobId, router]);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-lg">Analiz yükleniyor...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error}
        </div>
        <button
          onClick={() => router.back()}
          className="mt-4 text-blue-600 hover:text-blue-800"
        >
          ← Geri Dön
        </button>
      </div>
    );
  }

  if (!analysis) return null;

  const salaryCompColor = 
    analysis.salary_analysis.competitiveness === 'above' ? 'text-green-600' :
    analysis.salary_analysis.competitiveness === 'below' ? 'text-red-600' :
    'text-yellow-600';

  // Pasta grafiği için veri hazırla
  const workTypeData = Object.entries(analysis.work_type_analysis.market_distribution).map(([key, value]) => ({
    name: key,
    value: value
  }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div className="container mx-auto px-4 py-8">
      <button
        onClick={() => router.back()}
        className="mb-6 text-blue-600 hover:text-blue-800 flex items-center gap-2"
      >
        ← Geri Dön
      </button>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">İlan Rekabet Analizi</h1>
        <p className="text-gray-600">{analysis.job_title}</p>
        <p className="text-sm text-gray-500 mt-2">
          {analysis.total_similar_jobs} benzer ilan ile karşılaştırıldı
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Maaş Analizi */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Maaş Analizi</h2>
          
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600">Sizin Maaş Aralığınız</p>
              <p className="text-lg font-semibold">
                {analysis.salary_analysis.your_min && analysis.salary_analysis.your_max
                  ? `₺${analysis.salary_analysis.your_min.toLocaleString()} - ₺${analysis.salary_analysis.your_max.toLocaleString()}`
                  : 'Belirtilmemiş'}
              </p>
            </div>

            <div>
              <p className="text-sm text-gray-600">Piyasa Ortalaması</p>
              <p className="text-lg font-semibold">
                ₺{analysis.salary_analysis.market_avg_min.toLocaleString()} - ₺{analysis.salary_analysis.market_avg_max.toLocaleString()}
              </p>
            </div>

            <div className={`p-4 rounded-lg ${
              analysis.salary_analysis.competitiveness === 'above' ? 'bg-green-50' :
              analysis.salary_analysis.competitiveness === 'below' ? 'bg-red-50' :
              'bg-yellow-50'
            }`}>
              <p className={`font-semibold ${salaryCompColor}`}>
                {analysis.salary_analysis.message}
              </p>
            </div>

            {/* Basit Bar Grafiği */}
            {analysis.salary_analysis.your_min && analysis.salary_analysis.your_max && (
              <div className="mt-4">
                <div className="space-y-2">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Sizin İlanınız</span>
                      <span>₺{((analysis.salary_analysis.your_min + analysis.salary_analysis.your_max) / 2).toLocaleString()}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div 
                        className="bg-blue-600 h-3 rounded-full" 
                        style={{ 
                          width: `${Math.min(100, ((analysis.salary_analysis.your_min + analysis.salary_analysis.your_max) / 2) / ((analysis.salary_analysis.market_avg_min + analysis.salary_analysis.market_avg_max) / 2) * 100)}%` 
                        }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Piyasa Ortalaması</span>
                      <span>₺{((analysis.salary_analysis.market_avg_min + analysis.salary_analysis.market_avg_max) / 2).toLocaleString()}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div className="bg-green-600 h-3 rounded-full" style={{ width: '100%' }} />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Beceri Analizi */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Beceri Analizi</h2>
          
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 mb-2">Eşleşme Oranı</p>
              <div className="flex items-center gap-3">
                <div className="flex-1 bg-gray-200 rounded-full h-4">
                  <div 
                    className="bg-blue-600 h-4 rounded-full" 
                    style={{ width: `${analysis.skill_analysis.match_percentage}%` }}
                  />
                </div>
                <span className="font-semibold text-lg">
                  %{analysis.skill_analysis.match_percentage.toFixed(0)}
                </span>
              </div>
            </div>

            <div>
              <p className="text-sm font-semibold text-gray-700 mb-2">
                Piyasada Trend Beceriler
              </p>
              <div className="flex flex-wrap gap-2">
                {analysis.skill_analysis.trending_skills.slice(0, 8).map((skill, idx) => (
                  <span 
                    key={idx}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {analysis.skill_analysis.missing_skills.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-red-700 mb-2">
                  İlanınızda Eksik Beceriler
                </p>
                <div className="flex flex-wrap gap-2">
                  {analysis.skill_analysis.missing_skills.slice(0, 6).map((skill, idx) => (
                    <span 
                      key={idx}
                      className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Bu becerileri eklemek ilanınızı daha rekabetçi hale getirebilir
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Çalışma Tipi Analizi */}
        <div className="bg-white rounded-lg shadow p-6 md:col-span-2">
          <h2 className="text-xl font-semibold mb-4">Çalışma Tipi Analizi</h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-gray-600 mb-2">Sizin Çalışma Tipiniz</p>
              <p className="text-2xl font-bold text-blue-600 mb-4">
                {analysis.work_type_analysis.your_work_type}
              </p>
              
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-700">
                  {analysis.work_type_analysis.message}
                </p>
              </div>
            </div>

            <div>
              <p className="text-sm text-gray-600 mb-4">Piyasa Dağılımı</p>
              {workTypeData.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={workTypeData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: %${value.toFixed(0)}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {workTypeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-gray-500 text-center py-8">Veri bulunamadı</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
