"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User, FileText, Briefcase, Heart, Upload, X, Loader2, Target } from "lucide-react";
import { getCurrentUser } from "@/lib/api";

const getApiUrl = () => process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export default function ProfilePage() {
  const [profile, setProfile] = useState<any>(null);
  const [applications, setApplications] = useState<any[]>([]);
  const [favorites, setFavorites] = useState<any[]>([]);
  const [savedResumes, setSavedResumes] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzedData, setAnalyzedData] = useState<any>(null);
  const [showEditForm, setShowEditForm] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [previewFile, setPreviewFile] = useState<string | null>(null);
  const [editingResumeId, setEditingResumeId] = useState<number | null>(null);
  
  // PDF önizleme state'leri
  const [viewingPdfId, setViewingPdfId] = useState<number | null>(null);
  const [pdfPreviewUrls, setPdfPreviewUrls] = useState<Record<number, string>>({});

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem("accessToken");
      if (!token) return;

      try {
        const userData = await getCurrentUser(token);
        setProfile(userData);

        const apiUrl = getApiUrl();

        // Başvuruları yükle
        const appsResponse = await fetch(`${apiUrl}/my-applications`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (appsResponse.ok) {
          const appsData = await appsResponse.json();
          setApplications(appsData.applications || []);
        }

        // Favorileri yükle
        const favResponse = await fetch(`${apiUrl}/my-favorites`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (favResponse.ok) {
          const favData = await favResponse.json();
          setFavorites(favData.favorites || []);
        }

        // CV'leri yükle
        const resumeResponse = await fetch(`${apiUrl}/cv/my-resumes`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (resumeResponse.ok) {
          const resumes = await resumeResponse.json();
          setSavedResumes(resumes);
        }
      } catch (error) {
        console.error('Veri yüklenemedi:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === "application/pdf") {
      setSelectedFile(file);
    } else {
      alert("Lütfen sadece PDF dosyası seçin.");
    }
  };

  const handleAnalyzeCV = async () => {
    if (!selectedFile) return;

    const token = localStorage.getItem("accessToken");
    if (!token) {
      alert("Lütfen giriş yapın.");
      return;
    }

    setIsAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/cv/upload-and-analyze`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (!response.ok) throw new Error('CV analiz edilemedi');
      const result = await response.json();

      // PDF'i base64'e çevir
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviewFile(e.target?.result as string);
      };
      reader.readAsDataURL(selectedFile);

      const processedResult = {
        full_name: result.full_name || '',
        email: result.email || '',
        phone: result.phone || '',
        summary: result.summary || '',
        skills: result.skills || [],
        languages: result.languages || [],
        experiences: result.experiences || [],
        educations: result.educations || [],
        file_path: result.file_path || ''
      };

      setAnalyzedData(processedResult);
      setShowEditForm(true);
    } catch (err: any) {
      alert('Hata: ' + err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveAnalyzedCV = async () => {
    const token = localStorage.getItem("accessToken");
    if (!token || !analyzedData || !profile || isSaving) return;

    setIsSaving(true);
    try {
      const dataToSave = {
        ...analyzedData,
        full_name: profile.full_name,
        file_path: analyzedData.file_path || null
      };

      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/cv/confirm-and-save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(dataToSave)
      });

      if (!response.ok) throw new Error('CV kaydedilemedi');

      alert('CV başarıyla kaydedildi!');
      setShowEditForm(false);
      setAnalyzedData(null);
      setSelectedFile(null);
      setPreviewFile(null);
      
      // CV'leri yeniden yükle
      const resumeResponse = await fetch(`${apiUrl}/cv/my-resumes`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resumeResponse.ok) {
        const resumes = await resumeResponse.json();
        setSavedResumes(resumes);
      }
    } catch (err: any) {
      alert('CV kaydedilirken hata oluştu: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleFormChange = (field: string, value: any) => {
    setAnalyzedData({
      ...analyzedData,
      [field]: value
    });
  };

  const updateExperience = (index: number, field: string, value: string) => {
    if (!analyzedData?.experiences) return;
    const newExps = [...analyzedData.experiences];
    newExps[index] = { ...newExps[index], [field]: value };
    handleFormChange('experiences', newExps);
  };

  const updateEducation = (index: number, field: string, value: string) => {
    if (!analyzedData?.educations) return;
    const newEdus = [...analyzedData.educations];
    newEdus[index] = { ...newEdus[index], [field]: value };
    handleFormChange('educations', newEdus);
  };

  const handleEditResume = (resume: any) => {
    setAnalyzedData({
      full_name: resume.full_name || '',
      email: resume.email || '',
      phone: resume.phone || '',
      summary: resume.summary || '',
      skills: resume.skills || [],
      languages: resume.languages || [],
      experiences: resume.experiences || [],
      educations: resume.educations || []
    });
    setEditingResumeId(resume.id);
    setShowEditForm(true);
  };

  const handleUpdateResume = async () => {
    const token = localStorage.getItem("accessToken");
    if (!token || !analyzedData || !editingResumeId || isSaving) return;

    setIsSaving(true);
    try {
      const payload = {
        full_name: analyzedData.full_name || '',
        email: analyzedData.email || '',
        phone: analyzedData.phone || '',
        summary: analyzedData.summary || '',
        skills: analyzedData.skills || [],
        languages: analyzedData.languages || [],
        experiences: (analyzedData.experiences || []).map((exp: any) => ({
          company: exp.company || '',
          position: exp.position || '',
          start_date: exp.start_date || '',
          end_date: exp.end_date || '',
          description: exp.description || ''
        })),
        educations: (analyzedData.educations || []).map((edu: any) => ({
          institution: edu.institution || '',
          degree: edu.degree || '',
          field: edu.field || '',
          start_date: edu.start_date || '',
          end_date: edu.end_date || ''
        }))
      };

      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/cv/resume/${editingResumeId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) throw new Error('CV güncellenemedi');

      alert('CV başarıyla güncellendi!');
      setShowEditForm(false);
      setAnalyzedData(null);
      setEditingResumeId(null);
      
      // CV'leri yeniden yükle
      const resumeResponse = await fetch(`${apiUrl}/cv/my-resumes`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (resumeResponse.ok) {
        const resumes = await resumeResponse.json();
        setSavedResumes(resumes);
      }
    } catch (err: any) {
      alert('CV güncellenirken hata oluştu: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleTogglePdfPreview = async (resumeId: number) => {
    if (viewingPdfId === resumeId) {
      setViewingPdfId(null);
      return;
    }

    if (pdfPreviewUrls[resumeId]) {
      setViewingPdfId(resumeId);
      return;
    }

    const token = localStorage.getItem("accessToken");
    if (!token) return;

    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/cv/resume/${resumeId}/pdf`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) {
         if (response.status === 404) {
             alert('Uyarı: Bu CV\'nin fiziksel PDF dosyası sistemde bulunmuyor (Eski kayıt).');
             return;
         }
         throw new Error('PDF alınamadı');
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setPdfPreviewUrls(prev => ({ ...prev, [resumeId]: url }));
      setViewingPdfId(resumeId);
    } catch (err: any) {
      alert("Hata: " + err.message);
    }
  };

  const handleDeleteResume = async (resumeId: number) => {
    if (!window.confirm('Bu CV\'yi silmek istediğinize emin misiniz?')) return;
    
    const token = localStorage.getItem("accessToken");
    if (!token) return;

    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/cv/resume/${resumeId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('CV silinemedi');

      setSavedResumes(prev => prev.filter((r: any) => r.id !== resumeId));
      if (viewingPdfId === resumeId) setViewingPdfId(null);
    } catch (err: any) {
      alert("Hata: " + err.message);
    }
  };

  if (isLoading) return <div className="container mx-auto py-8 text-center">Yükleniyor...</div>;
  if (!profile) return <div className="container mx-auto py-8 text-center">Profil bulunamadı.</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Profilim</h1>
          <p className="text-gray-600 mt-1">Bilgilerinizi ve başvurularınızı yönetin</p>
        </div>

        <Tabs defaultValue="info" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-[600px]">
            <TabsTrigger value="info" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              <span className="hidden sm:inline">Bilgilerim</span>
            </TabsTrigger>
            <TabsTrigger value="cv" className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              <span className="hidden sm:inline">CV'lerim</span>
            </TabsTrigger>
            <TabsTrigger value="applications" className="flex items-center gap-2">
              <Briefcase className="h-4 w-4" />
              <span className="hidden sm:inline">Başvurularım</span>
              {applications.length > 0 && (
                <span className="ml-1 bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
                  {applications.length}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="favorites" className="flex items-center gap-2">
              <Heart className="h-4 w-4" />
              <span className="hidden sm:inline">Favorilerim</span>
              {favorites.length > 0 && (
                <span className="ml-1 bg-red-600 text-white text-xs px-2 py-0.5 rounded-full">
                  {favorites.length}
                </span>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="info">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Kişisel Bilgiler</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-semibold text-2xl">
                        {profile.full_name?.charAt(0) || 'U'}
                      </span>
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold">{profile.full_name}</h3>
                      <p className="text-gray-600">{profile.profession || "Meslek belirtilmemiş"}</p>
                    </div>
                  </div>
                  <div className="grid md:grid-cols-2 gap-4 pt-4">
                    <div>
                      <p className="text-sm text-gray-600">E-posta</p>
                      <p className="font-medium">{profile.email}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Doğum Tarihi</p>
                      <p className="font-medium">{profile.date_of_birth || "Belirtilmemiş"}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {savedResumes.length > 0 && savedResumes[0] && (
                <Card>
                  <CardHeader>
                    <CardTitle>CV Bilgilerim</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {savedResumes[0].summary && (
                      <div>
                        <h4 className="font-semibold text-sm text-gray-700 mb-2">Profesyonel Özet</h4>
                        <p className="text-sm text-gray-800 leading-relaxed bg-gray-50 p-3 rounded">
                          {savedResumes[0].summary}
                        </p>
                      </div>
                    )}

                    <div className="grid md:grid-cols-2 gap-6">
                      {savedResumes[0].skills && savedResumes[0].skills.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-sm text-gray-700 mb-2">Yetenekler</h4>
                          <div className="flex flex-wrap gap-2">
                            {savedResumes[0].skills.map((skill: string, idx: number) => (
                              <span key={idx} className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {savedResumes[0].languages && savedResumes[0].languages.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-sm text-gray-700 mb-2">Diller</h4>
                          <div className="flex flex-wrap gap-2">
                            {savedResumes[0].languages.map((lang: any, idx: number) => (
                              <span key={idx} className="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">
                                {typeof lang === 'string' ? lang : `${lang.name}${lang.proficiency ? ` (${lang.proficiency})` : ''}`}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {savedResumes[0].experiences && savedResumes[0].experiences.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-sm text-gray-700 mb-3">Deneyimler</h4>
                        <div className="space-y-3">
                          {savedResumes[0].experiences.map((exp: any, idx: number) => (
                            <div key={idx} className="bg-gray-50 p-4 rounded-lg border-l-4 border-blue-500">
                              <div className="flex justify-between items-start mb-2">
                                <div>
                                  <p className="font-semibold">{exp.position}</p>
                                  <p className="text-sm text-blue-600">{exp.company}</p>
                                </div>
                                <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded">
                                  {exp.start_date} - {exp.end_date}
                                </span>
                              </div>
                              {exp.description && (
                                <p className="text-sm text-gray-700">{exp.description}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {savedResumes[0].educations && savedResumes[0].educations.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-sm text-gray-700 mb-3">Eğitim</h4>
                        <div className="space-y-3">
                          {savedResumes[0].educations.map((edu: any, idx: number) => (
                            <div key={idx} className="bg-gray-50 p-4 rounded-lg border-l-4 border-orange-500">
                              <div className="flex justify-between items-start mb-1">
                                <div>
                                  <p className="font-semibold">{edu.institution}</p>
                                  <p className="text-sm text-orange-600">{edu.degree} - {edu.field}</p>
                                </div>
                                <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded">
                                  {edu.start_date} - {edu.end_date}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          <TabsContent value="cv">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>CV Yükle ve Analiz Et</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="border-2 border-dashed border-blue-200 rounded-xl p-8 text-center bg-blue-50/50">
                    {selectedFile ? (
                      <div className="space-y-4">
                        <div className="flex items-center justify-center gap-3">
                          <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                            <FileText className="h-6 w-6 text-blue-600" />
                          </div>
                          <div className="text-left">
                            <p className="font-medium text-gray-900">{selectedFile.name}</p>
                            <p className="text-sm text-gray-500">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedFile(null)}
                            className="ml-auto"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                        <Button
                          onClick={handleAnalyzeCV}
                          disabled={isAnalyzing}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          {isAnalyzing ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Analiz Ediliyor...
                            </>
                          ) : (
                            <>
                              <Upload className="mr-2 h-4 w-4" />
                              Analiz Et
                            </>
                          )}
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                          <Upload className="h-8 w-8 text-blue-600" />
                        </div>
                        <div>
                          <p className="text-lg font-medium text-gray-900">CV'nizi yükleyin</p>
                          <p className="text-sm text-gray-500 mt-1">
                            PDF formatında CV yükleyin, otomatik analiz edilsin
                          </p>
                        </div>
                        <div>
                          <Input
                            type="file"
                            accept=".pdf"
                            onChange={handleFileSelect}
                            className="hidden"
                            id="cv-upload"
                          />
                          <Label htmlFor="cv-upload" className="cursor-pointer">
                            <Button variant="outline" type="button" asChild>
                              <span>
                                <Upload className="mr-2 h-4 w-4" />
                                Dosya Seç
                              </span>
                            </Button>
                          </Label>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Kayıtlı CV'lerim ({savedResumes.length})</CardTitle>
                </CardHeader>
                <CardContent>
                {savedResumes.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">Henüz kayıtlı CV'niz yok</p>
                ) : (
                  <div className="space-y-4">
                    {savedResumes.map((resume: any) => (
                      <div key={resume.id} className="border rounded-lg p-4 hover:bg-gray-50 flex flex-col gap-2">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-semibold">{resume.full_name}</h4>
                          <div className="flex gap-2 flex-wrap items-center justify-end">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleTogglePdfPreview(resume.id)}
                              className={`${viewingPdfId === resume.id ? 'bg-purple-100 border-purple-300 text-purple-800' : 'text-purple-600 border-purple-200 hover:bg-purple-50'}`}
                            >
                              <FileText className="h-4 w-4 mr-2" />
                              {viewingPdfId === resume.id ? 'Kaldır' : 'PDF Önizleme'}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => window.location.href = `/profile/ats-report?cvId=${resume.id}`}
                              className="text-blue-600 border-blue-200 hover:bg-blue-50"
                            >
                              <Target className="h-4 w-4 mr-2" />
                              ATS Analizi
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEditResume(resume)}
                              className="text-gray-600"
                            >
                              Düzenle
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDeleteResume(resume.id)}
                              className="text-red-600 border-red-200 hover:bg-red-50"
                            >
                              <X className="h-4 w-4 mr-1" />
                              Sil
                            </Button>
                          </div>
                        </div>
                        {resume.summary && (
                          <p className="text-sm text-gray-600 mb-3">{resume.summary}</p>
                        )}
                        {resume.skills && resume.skills.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            {resume.skills.slice(0, 5).map((skill: string, idx: number) => (
                              <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                {skill}
                              </span>
                            ))}
                            {resume.skills.length > 5 && (
                              <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                                +{resume.skills.length - 5} daha
                              </span>
                            )}
                          </div>
                        )}
                        
                        {/* Inline PDF Viewer */}
                        {viewingPdfId === resume.id && pdfPreviewUrls[resume.id] && (
                           <div className="w-full h-[600px] border-2 border-slate-200 rounded-lg overflow-hidden mt-4 shadow-inner">
                             <div className="bg-slate-100 p-2 text-xs font-semibold text-slate-500 border-b">
                               Doğrudan Cihazınız Üzerinden Güvenli Önizleme
                             </div>
                             <iframe src={pdfPreviewUrls[resume.id]} className="w-full h-full bg-white" title="PDF Önizleme" />
                           </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
            </div>
          </TabsContent>

          <TabsContent value="applications">
            <Card>
              <CardHeader>
                <CardTitle>Başvurularım ({applications.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {applications.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">Henüz başvurunuz yok</p>
                ) : (
                  <div className="space-y-3">
                    {applications.map((app: any) => (
                      <div
                        key={app.id}
                        className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                        onClick={() => window.location.href = `/jobs/${app.job_id}`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h4 className="font-semibold text-lg">{app.job_title}</h4>
                            <p className="text-gray-600">{app.company_name}</p>
                          </div>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                            app.status === 'accepted' ? 'bg-green-100 text-green-800' :
                            app.status === 'rejected' ? 'bg-red-100 text-red-800' :
                            app.status === 'reviewed' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {app.status === 'pending' ? 'Beklemede' :
                             app.status === 'reviewed' ? 'İncelendi' :
                             app.status === 'accepted' ? 'Kabul Edildi' :
                             app.status === 'rejected' ? 'Reddedildi' : app.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          {app.job_location && <span>{app.job_location}</span>}
                          {app.job_type && <span>{app.job_type}</span>}
                          <span>{new Date(app.applied_at).toLocaleDateString('tr-TR')}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="favorites">
            <Card>
              <CardHeader>
                <CardTitle>Favori İlanlarım ({favorites.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {favorites.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">Henüz favori ilanınız yok</p>
                ) : (
                  <div className="space-y-3">
                    {favorites.map((job: any) => (
                      <div
                        key={job.id}
                        className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                        onClick={() => window.location.href = `/jobs/${job.id}`}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h4 className="font-semibold text-lg">{job.title}</h4>
                            <p className="text-gray-600">{job.company_name}</p>
                          </div>
                          <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium">
                            Favori
                          </span>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                          {job.location && <span>{job.location}</span>}
                          {job.work_type && <span>{job.work_type}</span>}
                          {job.job_type && <span>{job.job_type}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {showEditForm && analyzedData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] flex overflow-hidden">
            {/* Sol taraf - PDF Önizleme */}
            {previewFile && (
              <div className="w-1/2 border-r flex flex-col">
                <div className="p-4 border-b flex justify-between items-center">
                  <h3 className="font-semibold">CV Önizleme</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = previewFile;
                      link.download = selectedFile?.name || 'cv.pdf';
                      link.click();
                    }}
                  >
                    İndir
                  </Button>
                </div>
                <div className="flex-1 overflow-hidden">
                  <iframe
                    src={previewFile}
                    className="w-full h-full"
                    title="CV Önizleme"
                  />
                </div>
              </div>
            )}
            
            {/* Sağ taraf - Düzenleme Formu */}
            <div className={`${previewFile ? 'w-1/2' : 'w-full'} flex flex-col`}>
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">
                {editingResumeId ? 'CV Düzenle' : 'CV Analiz Sonucu - Kontrol Edin'}
              </h3>
              <Button variant="ghost" size="sm" onClick={() => {
                setShowEditForm(false);
                setEditingResumeId(null);
                setPreviewFile(null);
              }}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 p-4 overflow-y-auto space-y-4">
              <div className="space-y-2">
                <h4 className="font-medium">Kişisel Bilgiler</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>E-posta</Label>
                    <Input
                      value={analyzedData.email || ''}
                      onChange={(e) => handleFormChange('email', e.target.value)}
                    />
                  </div>
                  <div>
                    <Label>Telefon</Label>
                    <Input
                      value={analyzedData.phone || ''}
                      onChange={(e) => handleFormChange('phone', e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Profesyonel Özet</Label>
                <textarea
                  className="w-full p-2 border rounded-md min-h-[100px]"
                  value={analyzedData.summary || ''}
                  onChange={(e) => handleFormChange('summary', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Yetenekler</Label>
                <div className="flex flex-wrap gap-2">
                  {(analyzedData.skills || []).map((skill: string, index: number) => (
                    <div key={index} className="flex items-center gap-1 bg-blue-100 px-2 py-1 rounded">
                      <span className="text-sm">{skill}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-4 w-4 p-0"
                        onClick={() => {
                          const newSkills = analyzedData.skills.filter((_: any, i: number) => i !== index);
                          handleFormChange('skills', newSkills);
                        }}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
                <Input
                  placeholder="Yeni yetenek ekle ve Enter'a bas"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const value = (e.currentTarget.value).trim();
                      if (value) {
                        const newSkills = [...(analyzedData.skills || []), value];
                        handleFormChange('skills', newSkills);
                        e.currentTarget.value = '';
                      }
                    }
                  }}
                />
              </div>

              <div className="space-y-2">
                <Label>Diller</Label>
                <div className="flex flex-wrap gap-2">
                  {(analyzedData.languages || []).map((language: string, index: number) => (
                    <div key={index} className="flex items-center gap-1 bg-green-100 px-2 py-1 rounded">
                      <span className="text-sm">{language}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-4 w-4 p-0"
                        onClick={() => {
                          const newLangs = analyzedData.languages.filter((_: any, i: number) => i !== index);
                          handleFormChange('languages', newLangs);
                        }}
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
                <Input
                  placeholder="Yeni dil ekle ve Enter'a bas"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const value = (e.currentTarget.value).trim();
                      if (value) {
                        const newLangs = [...(analyzedData.languages || []), value];
                        handleFormChange('languages', newLangs);
                        e.currentTarget.value = '';
                      }
                    }
                  }}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Deneyimler</Label>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const newExp = {
                        company: '',
                        position: '',
                        start_date: '',
                        end_date: '',
                        description: ''
                      };
                      const newExps = [...(analyzedData.experiences || []), newExp];
                      handleFormChange('experiences', newExps);
                    }}
                  >
                    + Deneyim Ekle
                  </Button>
                </div>
                {(analyzedData.experiences || []).map((exp: any, index: number) => (
                  <div key={index} className="border p-3 rounded space-y-2 relative">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute top-2 right-2 h-6 w-6 p-0"
                      onClick={() => {
                        const newExps = analyzedData.experiences.filter((_: any, i: number) => i !== index);
                        handleFormChange('experiences', newExps);
                      }}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                    <div className="grid grid-cols-2 gap-2">
                      <Input
                        placeholder="Şirket"
                        value={exp.company || ''}
                        onChange={(e) => updateExperience(index, 'company', e.target.value)}
                      />
                      <Input
                        placeholder="Pozisyon"
                        value={exp.position || ''}
                        onChange={(e) => updateExperience(index, 'position', e.target.value)}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <Input
                        placeholder="Başlangıç (2020)"
                        value={exp.start_date || ''}
                        onChange={(e) => updateExperience(index, 'start_date', e.target.value)}
                      />
                      <Input
                        placeholder="Bitiş (2023)"
                        value={exp.end_date || ''}
                        onChange={(e) => updateExperience(index, 'end_date', e.target.value)}
                      />
                    </div>
                    <textarea
                      className="w-full p-2 border rounded-md"
                      placeholder="Açıklama"
                      rows={3}
                      value={exp.description || ''}
                      onChange={(e) => updateExperience(index, 'description', e.target.value)}
                    />
                  </div>
                ))}
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Eğitim</Label>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const newEdu = {
                        institution: '',
                        degree: '',
                        field: '',
                        start_date: '',
                        end_date: ''
                      };
                      const newEdus = [...(analyzedData.educations || []), newEdu];
                      handleFormChange('educations', newEdus);
                    }}
                  >
                    + Eğitim Ekle
                  </Button>
                </div>
                {(analyzedData.educations || []).map((edu: any, index: number) => (
                  <div key={index} className="border p-3 rounded space-y-2 relative">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute top-2 right-2 h-6 w-6 p-0"
                      onClick={() => {
                        const newEdus = analyzedData.educations.filter((_: any, i: number) => i !== index);
                        handleFormChange('educations', newEdus);
                      }}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                    <div className="grid grid-cols-3 gap-2">
                      <Input
                        placeholder="Kurum"
                        value={edu.institution || ''}
                        onChange={(e) => updateEducation(index, 'institution', e.target.value)}
                      />
                      <Input
                        placeholder="Derece"
                        value={edu.degree || ''}
                        onChange={(e) => updateEducation(index, 'degree', e.target.value)}
                      />
                      <Input
                        placeholder="Bölüm"
                        value={edu.field || ''}
                        onChange={(e) => updateEducation(index, 'field', e.target.value)}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <Input
                        placeholder="Başlangıç (2015)"
                        value={edu.start_date || ''}
                        onChange={(e) => updateEducation(index, 'start_date', e.target.value)}
                      />
                      <Input
                        placeholder="Bitiş (2019)"
                        value={edu.end_date || ''}
                        onChange={(e) => updateEducation(index, 'end_date', e.target.value)}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex gap-2 p-4 border-t">
              <Button
                onClick={editingResumeId ? handleUpdateResume : handleSaveAnalyzedCV}
                disabled={isSaving}
                className="bg-green-600 hover:bg-green-700"
              >
                {isSaving ? 'Kaydediliyor...' : editingResumeId ? 'Güncelle' : 'Onayla ve Kaydet'}
              </Button>
              <Button variant="outline" onClick={() => {
                setShowEditForm(false);
                setEditingResumeId(null);
                setPreviewFile(null);
              }}>
                İptal
              </Button>
            </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
