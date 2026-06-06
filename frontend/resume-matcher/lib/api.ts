import { z } from "zod";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

const RegisterUserSchema = z.object({
  fullName: z.string().min(2, "İsim en az 2 karakter olmalıdır."),
  email: z.string().email("Geçersiz e-posta adresi."),
  password: z.string().min(6, "Şifre en az 6 karakter olmalıdır."),
  userRole: z.enum(["aday", "isveren"]),
  dateOfBirth: z.string().optional(),
  profession: z.string().optional(),
});

export type RegisterUserInput = z.infer<typeof RegisterUserSchema>;

export interface JobPosting {
  id: number;
  title: string;
  company_name: string;
  description?: string;
  requirements?: string;
  skills_required?: string;
  location?: string;
  work_type?: string;
  job_type?: string;
  experience_level?: string;
  salary_min?: number;
  salary_max?: number;
  sector?: string;
  is_active: boolean;
  created_at: string;
  created_by: number;
}

export interface JobPostingWithScore extends JobPosting {
  match_score: number;
}

export interface JobMatchResponse {
  matches: JobPostingWithScore[];
  total_jobs: number;
  processing_time: number;
}

export interface ATSScoreResponse {
  overall_score: number;
  layout_score: number;
  content_score: number;
  action_verb_count: number;
  improvement_suggestions: string[];
  compliance_level: string;
  feedback: { type: string; message: string }[];
  analyzed_at: string;
}


export const registerUser = async (userData: RegisterUserInput) => {
  const validatedData = RegisterUserSchema.parse(userData);

  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      full_name: validatedData.fullName,
      email: validatedData.email,
      password: validatedData.password,
      user_role: validatedData.userRole,
      date_of_birth: validatedData.dateOfBirth || null,
      profession: validatedData.profession || null,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Kayıt başarısız oldu.");
  }

  return await response.json();
};

const LoginUserSchema = z.object({
  email: z.string().email("Geçersiz e-posta adresi."),
  password: z.string().min(1, "Şifre boş olamaz."),
});

export type LoginUserInput = z.infer<typeof LoginUserSchema>;

export const loginUser = async (credentials: LoginUserInput) => {
  const validatedData = LoginUserSchema.parse(credentials);

  const body = new URLSearchParams();
  body.append("username", validatedData.email);
  body.append("password", validatedData.password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: body,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(
      errorData.detail ||
      "Giriş başarısız oldu. Lütfen bilgilerinizi kontrol edin."
    );
  }

  return await response.json();
};

export const getCurrentUser = async (token: string) => {
  const response = await fetch(`${API_BASE_URL}/users/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Kullanıcı bilgileri alınamadı.");
  }

  return await response.json();
};

const UpdateUserSchema = z.object({
  full_name: z.string().optional(),
  date_of_birth: z.string().optional(),
  profession: z.string().optional(),
});

export type UpdateUserInput = z.infer<typeof UpdateUserSchema>;

export const updateCurrentUser = async (
  token: string,
  userData: UpdateUserInput
) => {
  const response = await fetch(`${API_BASE_URL}/users/me`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(userData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Güncelleme başarısız oldu.");
  }

  return await response.json();
};

export const matchJobsWithCV = async (
  token: string,
  cvProfileId: number,
  limit: number = 10
): Promise<JobMatchResponse> => {
  const response = await fetch(`${API_BASE_URL}/match-jobs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      cv_profile_id: cvProfileId,
      limit: limit,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "İş eşleştirme başarısız oldu.");
  }

  return await response.json();
};

export const getJobPostings = async (
  skip: number = 0,
  limit: number = 20
): Promise<JobPosting[]> => {
  const response = await fetch(
    `${API_BASE_URL}/jobs?skip=${skip}&limit=${limit}`,
    {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  if (!response.ok) {
    throw new Error("İş ilanları alınamadı.");
  }

  return await response.json();
};

export const uploadCV = async (token: string, file: File) => {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/cv/upload-and-analyze`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "CV yükleme başarısız oldu.");
  }

  return await response.json();
};

export const getMyCVs = async (token: string) => {
  const response = await fetch(`${API_BASE_URL}/cv/my-cvs`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("CV'ler alınamadı.");
  }

  return await response.json();
};

export const deleteCV = async (token: string, cvId: number) => {
  const response = await fetch(`${API_BASE_URL}/cv/${cvId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "CV silme başarısız oldu.");
  }

  return await response.json();
};

export const getJobById = async (jobId: number): Promise<JobPosting> => {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);

  if (!response.ok) {
    throw new Error("İş ilanı bulunamadı.");
  }

  return await response.json();
};

export const createJob = async (token: string, jobData: Partial<JobPosting>) => {
  const response = await fetch(`${API_BASE_URL}/jobs/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(jobData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "İş ilanı oluşturulamadı.");
  }

  return await response.json();
};

export const updateJob = async (token: string, jobId: number, jobData: Partial<JobPosting>) => {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(jobData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "İş ilanı güncellenemedi.");
  }

  return await response.json();
};

export const deleteJob = async (token: string, jobId: number) => {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "İş ilanı silinemedi.");
  }

  return true;
};

export interface CandidateMatch {
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

export interface CandidatesResponse {
  candidates: CandidateMatch[];
  total_candidates: number;
  matched_candidates: number;
  processing_time: number;
}

export interface DetailedMatchAnalysis {
  overall_score: number;
  score_label: string;
  summary_text: string;
  base_similarity: number;
  skill_analysis: {
    score: number;
    matched_skills: string[];
    missing_skills: string[];
    extra_skills: string[];
    match_percentage: number;
  };
  education_analysis: {
    score: number;
    status: string;
    message: string;
    education_type: string;
    job_type: string;
  };
  experience_analysis: {
    score: number;
    status: string;
    message: string;
    candidate_years: number;
    required_years: number;
    experience_level: string;
  };
  critical_analysis: {
    score: number;
    status: string;
    message: string;
    role: string | null;
    required_skills: string[];
    found_skills: string[];
    missing_skills?: string[];
    coverage_percentage?: number;
  };
  recommendations: string[];
}

export interface DetailedMatchResponse {
  job: {
    id: number;
    title: string;
    company_name: string;
    experience_level: string;
    skills_required: string;
  };
  candidate: {
    resume_id: number;
    full_name: string;
    email: string;
    skills: string;
    experience_count: number;
    education: string;
  };
  analysis: DetailedMatchAnalysis;
}

export const getCandidatesForJob = async (
  token: string,
  jobId: number,
  limit: number = 50
): Promise<CandidatesResponse> => {
  const response = await fetch(
    `${API_BASE_URL}/jobs/${jobId}/matches?limit=${limit}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Adaylar alınamadı.");
  }
  return response.json();
};

export const getDetailedMatch = async (
  token: string,
  jobId: number,
  resumeId: number
): Promise<DetailedMatchResponse> => {
  const response = await fetch(
    `${API_BASE_URL}/matches/${jobId}/${resumeId}`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Detaylı analiz alınamadı.");
  }
  return response.json();
};

// Axios benzeri API helper
export const api = {
  get: async (endpoint: string) => {
    const token = localStorage.getItem("accessToken");
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        Authorization: token ? `Bearer ${token}` : "",
      },
    });
    if (!response.ok) throw new Error("Request failed");
    return { data: await response.json() };
  },
  post: async (endpoint: string, data?: any) => {
    const token = localStorage.getItem("accessToken");
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: token ? `Bearer ${token}` : "",
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) throw new Error("Request failed");
    return { data: await response.json() };
  },
  put: async (endpoint: string, data?: any) => {
    const token = localStorage.getItem("accessToken");
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: token ? `Bearer ${token}` : "",
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) throw new Error("Request failed");
    return { data: await response.json() };
  },
  delete: async (endpoint: string) => {
    const token = localStorage.getItem("accessToken");
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
      headers: {
        Authorization: token ? `Bearer ${token}` : "",
      },
    });
    if (!response.ok) throw new Error("Request failed");
    return { data: await response.json() };
  },
};

// --- Messaging API ---

export interface ConversationResponse {
  other_user_id: number;
  other_user_name: string;
  last_message: string;
  last_message_at: string;
  unread_count: number;
}

export interface MessageResponse {
  id: number;
  sender_id: number;
  receiver_id: number;
  job_id: number | null;
  content: string;
  is_read: boolean;
  created_at: string;
}

export const getConversations = async (token: string): Promise<ConversationResponse[]> => {
  const response = await fetch(`${API_BASE_URL}/messages/conversations`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Konuşmalar alınamadı.");
  return response.json();
};

export const getMessagesWithUser = async (token: string, userId: number): Promise<MessageResponse[]> => {
  const response = await fetch(`${API_BASE_URL}/messages/conversation/${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Mesajlar alınamadı.");
  return response.json();
};

export const sendMessage = async (
  token: string,
  receiverId: number,
  content: string,
  jobId?: number
): Promise<MessageResponse> => {
  const response = await fetch(`${API_BASE_URL}/messages/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      receiver_id: receiverId,
      job_id: jobId,
      content,
    }),
  });
  if (!response.ok) throw new Error("Mesaj gönderilemedi.");
  return response.json();
};

export const markConversationAsRead = async (token: string, userId: number) => {
  const response = await fetch(`${API_BASE_URL}/messages/conversation/${userId}/read`, {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Mesajlar okundu olarak işaretlenemedi.");
  return response.json();
};

// --- Competitor Analysis API ---

export interface SalaryAnalysis {
  your_min: number | null;
  your_max: number | null;
  market_avg_min: number;
  market_avg_max: number;
  competitiveness: string;
  message: string;
}

export interface SkillAnalysis {
  your_skills: string[];
  trending_skills: string[];
  missing_skills: string[];
  match_percentage: number;
}

export interface WorkTypeAnalysis {
  your_work_type: string;
  market_distribution: Record<string, number>;
  message: string;
}

export interface CompetitorAnalysisResponse {
  job_id: number;
  job_title: string;
  total_similar_jobs: number;
  salary_analysis: SalaryAnalysis;
  skill_analysis: SkillAnalysis;
  work_type_analysis: WorkTypeAnalysis;
}

export const getCompetitorAnalysis = async (
  jobId: string,
  token: string
): Promise<CompetitorAnalysisResponse> => {
  const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/competitor-analysis`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Analiz alınamadı.");
  }
  return response.json();
};

export const analyzeATS = async (token: string, cvId: number): Promise<ATSScoreResponse> => {
  const response = await fetch(`${API_BASE_URL}/cv/${cvId}/analyze-ats`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "ATS analizi başarısız oldu.");
  }
  return response.json();
};

export const getCareerAdvice = async (token: string, cvId: number): Promise<{ advice: string }> => {
  const response = await fetch(`${API_BASE_URL}/cv/${cvId}/career-advice`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Kariyer tavsiyesi alınamadı.");
  }
  return response.json();
};

export const sendCareerChatMessage = async (
  token: string, 
  cvId: number, 
  messages: {role: string, content: string}[]
): Promise<{ advice: string }> => {
  const response = await fetch(`${API_BASE_URL}/cv/${cvId}/career-chat`, {
    method: "POST",
    headers: { 
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}` 
    },
    body: JSON.stringify({ messages })
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Sohbet mesajı gönderilemedi.");
  }
  return response.json();
};