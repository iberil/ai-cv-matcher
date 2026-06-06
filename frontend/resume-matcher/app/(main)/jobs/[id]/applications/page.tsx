'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api';

interface Application {
  id: number;
  status: string;
  cover_letter: string | null;
  applied_at: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone: string | null;
  candidate_profession: string | null;
}

interface JobDetails {
  id: number;
  title: string;
  company_name: string;
}

export default function JobApplicationsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  
  const [applications, setApplications] = useState<Application[]>([]);
  const [job, setJob] = useState<JobDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [jobId]);

  const fetchData = async () => {
    try {
      const [appsRes, jobRes] = await Promise.all([
        api.get(`/jobs/${jobId}/applications`),
        api.get(`/jobs/${jobId}`)
      ]);
      setApplications(appsRes.data);
      setJob(jobRes.data);
    } catch (error) {
      console.error('Veri yüklenirken hata:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (applicationId: number, status: string) => {
    try {
      await api.put(`/applications/${applicationId}/status`, { status });
      fetchData();
    } catch (error) {
      console.error('Durum güncellenirken hata:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'reviewed': return 'bg-blue-100 text-blue-800';
      case 'accepted': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return 'Beklemede';
      case 'reviewed': return 'İncelendi';
      case 'accepted': return 'Kabul Edildi';
      case 'rejected': return 'Reddedildi';
      default: return status;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-lg">Yükleniyor...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <button
        onClick={() => router.back()}
        className="mb-6 text-blue-600 hover:text-blue-800 flex items-center gap-2"
      >
        ← Geri Dön
      </button>

      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Başvurular</h1>
        {job && (
          <p className="text-gray-600">
            {job.title} - {job.company_name}
          </p>
        )}
        <p className="text-sm text-gray-500 mt-2">
          Toplam {applications.length} başvuru
        </p>
      </div>

      {applications.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">Henüz başvuru yapılmamış.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {applications.map((app) => (
            <div key={app.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold">{app.candidate_name}</h3>
                  <p className="text-gray-600">{app.candidate_profession || 'Meslek belirtilmemiş'}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(app.status)}`}>
                  {getStatusText(app.status)}
                </span>
              </div>

              <div className="space-y-2 mb-4">
                <p className="text-sm">
                  <span className="font-medium">E-posta:</span>{' '}
                  <a href={`mailto:${app.candidate_email}`} className="text-blue-600 hover:underline">
                    {app.candidate_email}
                  </a>
                </p>
                {app.candidate_phone && (
                  <p className="text-sm">
                    <span className="font-medium">Telefon:</span>{' '}
                    <a href={`tel:${app.candidate_phone}`} className="text-blue-600 hover:underline">
                      {app.candidate_phone}
                    </a>
                  </p>
                )}
                <p className="text-sm text-gray-500">
                  Başvuru Tarihi: {new Date(app.applied_at).toLocaleDateString('tr-TR')}
                </p>
              </div>

              {app.cover_letter && (
                <div className="mb-4 p-4 bg-gray-50 rounded">
                  <p className="font-medium text-sm mb-2">Ön Yazı:</p>
                  <p className="text-sm text-gray-700">{app.cover_letter}</p>
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => updateStatus(app.id, 'reviewed')}
                  disabled={app.status === 'reviewed'}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm"
                >
                  İncelendi
                </button>
                <button
                  onClick={() => updateStatus(app.id, 'accepted')}
                  disabled={app.status === 'accepted'}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm"
                >
                  Kabul Et
                </button>
                <button
                  onClick={() => updateStatus(app.id, 'rejected')}
                  disabled={app.status === 'rejected'}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm"
                >
                  Reddet
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
