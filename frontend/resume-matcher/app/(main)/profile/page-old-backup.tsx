"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, Edit, FileText, X, Eye, ChevronDown, ChevronUp } from "lucide-react";
import { getCurrentUser, updateCurrentUser, UpdateUserInput } from "@/lib/api";

interface UserProfile {
  id: number;
  full_name: string;
  email: string;
  date_of_birth: string | null;
  profession: string | null;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<UpdateUserInput>({});
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [cvList, setCvList] = useState<any[]>([]);
  const [previewCV, setPreviewCV] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzedData, setAnalyzedData] = useState<any>(null);
  const [showEditForm, setShowEditForm] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedResumes, setSavedResumes] = useState<any[]>([]);
  const [showCVManagement, setShowCVManagement] = useState(false);
  const [favorites, setFavorites] = useState<any[]>([]);

  const refreshSavedResumes = async () => {
    const token = localStorage.getItem("accessToken");
    if (!token) return;

    try {
      const resumeResponse = await fetch('http://127.0.0.1:8000/api/v1/cv/my-resumes', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (resumeResponse.ok) {
        const resumes = await resumeResponse.json();
        setSavedResumes(resumes);
      }
    } catch (error) {
      console.error('CV yüklenemedi:', error);
    }
  };

  useEffect(() => {
    const fetchProfile = async () => {
      const token = localStorage.getItem("accessToken");
      if (!token) {
        setError("Lütfen giriş yapın.");
        setIsLoading(false);
        return;
      }

      try {
        const userData = await getCurrentUser(token);
        setProfile(userData);
        setFormData({
          full_name: userData.full_name,
          date_of_birth: userData.date_of_birth,
          profession: userData.profession,
        });

        const userCVKey = `userCVs_${userData.id}`;
        const savedCVs = JSON.parse(localStorage.getItem(userCVKey) || '[]');
        setCvList(savedCVs);

        await refreshSavedResumes();
        
        // Favorileri yükle
        const favResponse = await fetch('http://127.0.0.1:8000/api/v1/my-favorites', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (favResponse.ok) {
          const favData = await favResponse.json();
          setFavorites(favData.favorites || []);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === "application/pdf") {
      setSelectedFile(file);
    } else {
      alert("Lütfen sadece PDF dosyası seçin.");
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const cvData = {
          id: Date.now(),
          name: selectedFile.name,
          size: selectedFile.size,
          uploadDate: new Date().toISOString(),
          data: e.target?.result
        };

        const token = localStorage.getItem("accessToken");
        if (!token) return;

        const userData = await getCurrentUser(token);
        const userCVKey = `userCVs_${userData.id}`;

        const existingCVs = JSON.parse(localStorage.getItem(userCVKey) || '[]');
        existingCVs.push(cvData);
        localStorage.setItem(userCVKey, JSON.stringify(existingCVs));

        setCvList(existingCVs);
        alert("CV başarıyla yüklendi!");
        setSelectedFile(null);
      };
      reader.readAsDataURL(selectedFile);
    } catch (err: any) {
      alert("CV yüklenirken hata oluştu.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleAnalyzeCV = async (cv: any) => {
    const token = localStorage.getItem("accessToken");
    if (!token) {
      alert("Lütfen giriş yapın.");
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await fetch(cv.data);
      const blob = await response.blob();
      const formData = new FormData();
      formData.append('file', blob, cv.name);

      const apiResponse = await fetch('http://127.0.0.1:8000/api/v1/cv/upload-and-analyze', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (!apiResponse.ok) throw new Error('CV analiz edilemedi');
      const result = await apiResponse.json();

      const processedResult = {
        full_name: result.full_name || '',
        email: result.email || '',
        phone: result.phone || '',
        summary: result.summary || '',
        skills: result.skills || [],
        languages: result.languages || [],
        experiences: result.experiences || [],
        educations: result.educations || []
      };

      setAnalyzedData(processedResult);
      setShowEditForm(true);
    } catch (err: any) {
      alert('CV analiz edilirken hata oluştu: ' + err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveAnalyzedCV = async () => {
    const token = localStorage.getItem("accessToken");
    if (!token || !analyzedData || !profile || isSaving) return; // Çifte istek önleme

    setIsSaving(true);
    try {
      const dataToSave = {
        ...analyzedData,
        full_name: profile.full_name
      };

      const response = await fetch('http://127.0.0.1:8000/api/v1/cv/confirm-and-save', {
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
      await refreshSavedResumes();
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

  const handleDeleteCV = async (cvId: number) => {
    if (!confirm("Bu CV'yi silmek istediğinizden emin misiniz?")) return;

    const token = localStorage.getItem("accessToken");
    if (!token) return;

    const userData = await getCurrentUser(token);
    const userCVKey = `userCVs_${userData.id}`;

    const existingCVs = JSON.parse(localStorage.getItem(userCVKey) || '[]');
    const updatedCVs = existingCVs.filter((cv: any) => cv.id !== cvId);
    localStorage.setItem(userCVKey, JSON.stringify(updatedCVs));
    setCvList(updatedCVs);
    alert("CV başarıyla silindi!");
  };

  const handleDeleteSavedResume = async (resumeId: number) => {
    if (!confirm("Bu kayıtlı CV'yi silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.")) return;

    const token = localStorage.getItem("accessToken");
    if (!token) return;

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/v1/cv/resume/${resumeId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('CV silinemedi');

      alert("CV başarıyla silindi!");
      await refreshSavedResumes();
    } catch (err: any) {
      alert('Hata: ' + err.message);
    }
  };

  if (isLoading) return <div className="container mx-auto py-8 text-center">Yükleniyor...</div>;
  if (error) return <div className="container mx-auto py-8 text-center text-red-500">{error}</div>;
  if (!profile) return <div className="container mx-auto py-8 text-center">Profil bulunamadı.</div>;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto py-8 px-4 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Profilim</h1>
          <p className="text-gray-600 mt-1">Bilgilerinizi güncelleyin ve CV'nizi yönetin</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-12">
          <div className="lg:col-span-4">
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
              <CardHeader className="pb-4">
                <CardTitle className="text-xl text-gray-800">Kişisel Bilgiler</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-semibold text-lg">
                        {profile.full_name?.charAt(0) || 'U'}
                      </span>
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900">{profile.full_name}</p>
                      <p className="text-sm text-gray-500">{profile.profession || "Meslek belirtilmemiş"}</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-3 pt-4 border-t border-gray-100">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm text-gray-600">E-posta:</span>
                    <span className="text-sm font-medium text-gray-900">{profile.email}</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-gray-600">Doğum Tarihi:</span>
                    <span className="text-sm font-medium text-gray-900">
                      {profile.date_of_birth || "Belirtilmemiş"}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-8 space-y-6">
            <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between cursor-pointer" onClick={() => setShowCVManagement(!showCVManagement)}>
                  <CardTitle className="flex items-center gap-2 text-xl text-gray-800">
                    <FileText className="h-5 w-5 text-blue-600" />
                    CV Yönetimi
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <CardDescription className="text-gray-600 hidden md:block">
                      PDF formatında CV'nizi yükleyin ve analiz edin
                    </CardDescription>
                    {showCVManagement ? (
                      <ChevronUp className="h-5 w-5 text-gray-500" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-gray-500" />
                    )}
                  </div>
                </div>
              </CardHeader>
              {showCVManagement && (
                <CardContent className="space-y-6">
                  <div className="border-2 border-dashed border-blue-200 rounded-xl p-8 text-center bg-blue-50/50 hover:bg-blue-50 transition-colors">
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
                          onClick={handleFileUpload}
                          disabled={isUploading}
                          className="bg-blue-600 hover:bg-blue-700 shadow-md"
                        >
                          <Upload className="mr-2 h-4 w-4" />
                          {isUploading ? "Yükleniyor..." : "CV'yi Yükle"}
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
                            Sadece PDF dosyaları kabul edilir (Maks. 5MB)
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
                            <Button variant="outline" type="button" asChild className="border-blue-200 text-blue-600 hover:bg-blue-50">
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

                  {cvList.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="font-medium text-gray-800 flex items-center gap-2">
                        <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                        Yüklenmiş CV'ler
                      </h4>
                      <div className="space-y-3">
                        {cvList.map((cv: any) => (
                          <div key={cv.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-gray-50/50 hover:bg-gray-50 transition-colors">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                                <FileText className="h-5 w-5 text-orange-600" />
                              </div>
                              <div>
                                <p className="font-medium text-gray-900">{cv.name}</p>
                                <p className="text-sm text-gray-500">
                                  {new Date(cv.uploadDate).toLocaleDateString('tr-TR')} • {(cv.size / 1024).toFixed(1)} KB
                                </p>
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <Button
                                variant="default"
                                size="sm"
                                onClick={() => handleAnalyzeCV(cv)}
                                disabled={isAnalyzing}
                                className="bg-green-600 hover:bg-green-700 text-xs"
                              >
                                {isAnalyzing ? 'Analiz Ediliyor...' : 'Analiz Et'}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setPreviewCV(cv)}
                                className="text-xs"
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => {
                                  const link = document.createElement('a');
                                  link.href = cv.data;
                                  link.download = cv.name;
                                  link.click();
                                }}
                                className="text-xs"
                              >
                                İndir
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDeleteCV(cv.id)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50 text-xs"
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              )}
            </Card>
            {savedResumes.length > 0 && (
              <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xl text-gray-800 flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      CV Bilgilerim
                    </CardTitle>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={refreshSavedResumes}
                      className="border-blue-200 text-blue-600 hover:bg-blue-50"
                    >
                      Yenile
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {savedResumes.map((resume: any) => (
                    <div key={resume.id} className="space-y-4 p-4 bg-gray-50/50 rounded-lg border border-gray-100 relative">
                      <div className="absolute top-2 right-2 z-10">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            handleDeleteSavedResume(resume.id);
                          }}
                          className="text-red-500 hover:bg-red-50 hover:text-red-700 h-8 w-8 p-0 rounded-full cursor-pointer relative z-50"
                          title="CV'yi Sil"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                      {resume.summary && (
                        <div className="space-y-2">
                          <Label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                            Profesyonel Özet
                          </Label>
                          <p className="text-sm leading-relaxed text-gray-800 bg-white p-3 rounded border">{resume.summary}</p>
                        </div>
                      )}

                      <div className="grid md:grid-cols-2 gap-4">
                        {resume.skills && resume.skills.length > 0 && (
                          <div className="space-y-2">
                            <Label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                              Yetenekler ({resume.skills.length})
                            </Label>
                            <div className="flex flex-wrap gap-1">
                              {resume.skills.map((skill: string, idx: number) => (
                                <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full font-medium">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {resume.languages && resume.languages.length > 0 && (
                          <div className="space-y-2">
                            <Label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                              Diller ({resume.languages.length})
                            </Label>
                            <div className="flex flex-wrap gap-1">
                              {resume.languages.map((lang: any, idx: number) => (
                                <span key={idx} className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">
                                  {typeof lang === 'string' ? lang : `${lang.name}${lang.proficiency ? ` (${lang.proficiency})` : ''}`}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>

                      {resume.experiences && resume.experiences.length > 0 && (
                        <div className="space-y-3">
                          <Label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                            Deneyimler ({resume.experiences.length})
                          </Label>
                          <div className="space-y-3">
                            {resume.experiences.map((exp: any, idx: number) => (
                              <div key={idx} className="bg-white p-3 rounded border border-blue-100 border-l-4 border-l-blue-500">
                                <div className="flex justify-between items-start mb-2">
                                  <div>
                                    <p className="font-medium text-gray-900">{exp.position}</p>
                                    <p className="text-sm text-blue-600 font-medium">{exp.company}</p>
                                  </div>
                                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                    {exp.start_date} - {exp.end_date}
                                  </span>
                                </div>
                                {exp.description && (
                                  <p className="text-sm text-gray-700 leading-relaxed">{exp.description}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {resume.educations && resume.educations.length > 0 && (
                        <div className="space-y-3">
                          <Label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                            <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                            Eğitim ({resume.educations.length})
                          </Label>
                          <div className="space-y-3">
                            {resume.educations.map((edu: any, idx: number) => (
                              <div key={idx} className="bg-white p-3 rounded border border-orange-100 border-l-4 border-l-orange-500">
                                <div className="flex justify-between items-start mb-1">
                                  <div>
                                    <p className="font-medium text-gray-900">{edu.institution}</p>
                                    <p className="text-sm text-orange-600">{edu.degree} - {edu.field}</p>
                                  </div>
                                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                    {edu.start_date} - {edu.end_date}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
            
            {favorites.length > 0 && (
              <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
                <CardHeader className="pb-4">
                  <CardTitle className="text-xl text-gray-800 flex items-center gap-2">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                    Favori İlanlar ({favorites.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {favorites.map((job: any) => (
                    <div
                      key={job.id}
                      className="p-4 border border-gray-200 rounded-lg bg-gray-50/50 hover:bg-gray-50 transition-colors cursor-pointer"
                      onClick={() => window.location.href = `/jobs/${job.id}`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h4 className="font-medium text-gray-900">{job.title}</h4>
                          <p className="text-sm text-gray-600">{job.company_name}</p>
                          {job.location && (
                            <p className="text-xs text-gray-500 mt-1">{job.location}</p>
                          )}
                        </div>
                        <div className="text-right">
                          <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                            {job.work_type}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>

      {showEditForm && analyzedData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">CV Analiz Sonucu - Kontrol Edin</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowEditForm(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 p-4 overflow-y-auto space-y-4">
              {/* Kişisel Bilgiler */}
              <div className="space-y-2">
                <h4 className="font-medium">Kişisel Bilgiler</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Ad Soyad</Label>
                    <Input
                      value={analyzedData.full_name || ''}
                      onChange={(e) => handleFormChange('full_name', e.target.value)}
                    />
                  </div>
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

              {/* Özet */}
              <div className="space-y-2">
                <Label>Profesyonel Özet</Label>
                <textarea
                  className="w-full p-2 border rounded-md min-h-[100px]"
                  value={analyzedData.summary || ''}
                  onChange={(e) => handleFormChange('summary', e.target.value)}
                />
              </div>

              {/* Yetenekler */}
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

              {/* Diller */}
              <div className="space-y-2">
                <Label>Diller</Label>
                <div className="flex flex-wrap gap-2 p-2 border rounded-md min-h-[40px]">
                  {analyzedData.languages && analyzedData.languages.length > 0 ? (
                    analyzedData.languages.map((language: string, index: number) => (
                      <div key={index} className="bg-gray-100 text-gray-800 text-sm font-medium px-2.5 py-0.5 rounded-full flex items-center">
                        <span>{language}</span>
                        <button
                          type="button"
                          className="ml-2 text-gray-500 hover:text-gray-800"
                          onClick={() => {
                            const newLangs = analyzedData.languages.filter((_: any, i: number) => i !== index);
                            handleFormChange('languages', newLangs);
                          }}
                        >
                          &times;
                        </button>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-500 px-2 py-1">AI tarafından dil bulunamadı.</p>
                  )}
                </div>
                <Input
                  placeholder="Yeni dil ekle ve Enter'a bas (Örn: Almanca - B2)"
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

              {/* Deneyimler */}
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
                        if (!analyzedData?.experiences) return;
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
                        placeholder="Başlangıç Tarihi (2020)"
                        value={exp.start_date || ''}
                        onChange={(e) => updateExperience(index, 'start_date', e.target.value)}
                      />
                      <Input
                        placeholder="Bitiş Tarihi (2023)"
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

              {/* Eğitim */}
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
                        if (!analyzedData?.educations) return;
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
                        placeholder="Derece (Lisans/Yüksek Lisans)"
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
                        placeholder="Başlangıç Tarihi (2015)"
                        value={edu.start_date || ''}
                        onChange={(e) => updateEducation(index, 'start_date', e.target.value)}
                      />
                      <Input
                        placeholder="Bitiş Tarihi (2019)"
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
                onClick={handleSaveAnalyzedCV}
                disabled={isSaving}
                className="bg-green-600 hover:bg-green-700"
              >
                {isSaving ? 'Kaydediliyor...' : 'Onayla ve Kaydet'}
              </Button>
              <Button variant="outline" onClick={() => setShowEditForm(false)}>
                İptal
              </Button>
            </div>
          </div>
        </div>
      )}

      {previewCV && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">{previewCV.name}</h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPreviewCV(null)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 p-4">
              <iframe
                src={previewCV.data}
                className="w-full h-full min-h-[600px] border rounded"
                title="CV Önizleme"
              />
            </div>
            <div className="flex gap-2 p-4 border-t">
              <Button
                onClick={() => {
                  const link = document.createElement('a');
                  link.href = previewCV.data;
                  link.download = previewCV.name;
                  link.click();
                }}
              >
                İndir
              </Button>
              <Button
                variant="outline"
                onClick={() => setPreviewCV(null)}
              >
                Kapat
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}