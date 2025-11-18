'use client';

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Toaster, toast } from 'react-hot-toast';

import { useAppContext } from "../context/AppContext";
import { uploadCv, extractProfile, generateAdvice } from "../services/api";
import { ExtractedProfile, CareerAdviceResponse } from "../types";

import LearningPlan from "../components/LearningPlan";
import MultiStepUploadForm from "../components/MultiStepUploadForm";
import LoadingSpinner from "../components/LoadingSpinner";

type PageStatus = 'idle' | 'loading' | 'error' | 'success';

const ADVICE_STORAGE_KEY = 'careerAdvice';
const PROGRESS_STORAGE_KEY = 'careerProgress';

export default function UploadPage() {
  const router = useRouter();
  const { role, level, setRole, setLevel } = useAppContext();
  
  const [isHydrating, setIsHydrating] = useState(true);
  const [userId] = useState("default-user");

  const [file, setFile] = useState<File | null>(null);
  const [cvText, setCvText] = useState<string | null>(null);
  const [profile, setProfile] = useState<ExtractedProfile | null>(null);
  const [advice, setAdvice] = useState<CareerAdviceResponse | null>(null);
  const [completedWeeks, setCompletedWeeks] = useState<number[]>([]);
  const [status, setStatus] = useState<PageStatus>('idle');
  
  useEffect(() => {
    try {
      const savedAdvice = localStorage.getItem(ADVICE_STORAGE_KEY);
      const savedProgress = localStorage.getItem(PROGRESS_STORAGE_KEY);
      const savedRole = localStorage.getItem("user_role");
      const savedLevel = localStorage.getItem("user_level");

      if (savedAdvice) {
        setAdvice(JSON.parse(savedAdvice));
        setStatus('success');
      }
      if (savedProgress) {
        setCompletedWeeks(JSON.parse(savedProgress));
      }
      if (savedRole) setRole(savedRole);
      if (savedLevel) setLevel(savedLevel);

    } catch (error) {
      console.error("Failed to parse from localStorage", error);
      localStorage.clear();
    } finally {
      setIsHydrating(false);
    }
  }, [setRole, setLevel]);

  const handleGenerateAdvice = async () => {
    if (!profile || !role || !level) return;
    setStatus('loading');
    const toastId = toast.loading("Generating your roadmap...");
    try {
      const result = await generateAdvice({ profile, role, level });
      setAdvice(result.advice);
      setCompletedWeeks([]);
      localStorage.setItem(ADVICE_STORAGE_KEY, JSON.stringify(result.advice));
      localStorage.setItem("user_role", role);
      localStorage.setItem("user_level", level);
      localStorage.removeItem(PROGRESS_STORAGE_KEY);
      toast.success("Your career plan is ready!", { id: toastId });
      setStatus('success');
    } catch (error: any) {
      toast.error(error.message, { id: toastId });
      setStatus('error');
    }
  };

  const handleProgressUpdate = (newCompletedWeeks: number[]) => {
    setCompletedWeeks(newCompletedWeeks);
    localStorage.setItem(PROGRESS_STORAGE_KEY, JSON.stringify(newCompletedWeeks));
  };
  
  const handleStartOver = () => {
    if (confirm("Are you sure? This will permanently delete your current plan and progress.")) {
        setFile(null);
        setCvText(null);
        setProfile(null);
        setAdvice(null);
        setCompletedWeeks([]);
        setStatus('idle');
        
        localStorage.removeItem(ADVICE_STORAGE_KEY);
        localStorage.removeItem(PROGRESS_STORAGE_KEY);
        localStorage.removeItem("user_role");
        localStorage.removeItem("user_level");
        
        toast.success("Everything is reset. Let's set a new goal!");
        router.push("/onboarding");
    }
  };
  
  const handleUpload = async () => {
    if (!file) return toast.error("Please select a file first!");
    setStatus('loading');
    const toastId = toast.loading("Uploading CV...");
    try {
      const result = await uploadCv(file);
      setCvText(result.text);
      toast.success("CV text extracted!", { id: toastId });
      setStatus('idle');
    } catch (error: any) {
      toast.error(error.message, { id: toastId });
      setStatus('error');
    }
  };
  
  const handleAnalyze = async () => {
    if (!cvText) return;
    setStatus('loading');
    const toastId = toast.loading("Analyzing profile...");
    try {
      const result = await extractProfile(cvText);
      setProfile(result.profile);
      toast.success("Profile analysis complete!", { id: toastId });
      setStatus('idle');
    } catch (error: any) {
      toast.error(error.message, { id: toastId });
      setStatus('error');
    }
  };
  
  if (isHydrating) {
    return (
      <main className="min-h-screen w-full flex flex-col items-center justify-center p-4">
        <LoadingSpinner message="Loading your saved plan..." />
      </main>
    );
  }

if (advice) {
 return (
    <main className="min-h-screen w-full flex flex-col items-center p-4 md:p-8 bg-gray-50 text-gray-900">
      <Toaster position="top-center" />
      <div className="w-full max-w-4xl text-center mb-8">
        {/* DEĞİŞİKLİK 1: Başlığı daha dürüst ve odaklı hale getiriyoruz. */}
        <h1 className="text-3xl md:text-4xl font-bold text-gray-800">Your Foundational Roadmap</h1>
        {/* DEĞİŞİKLİK 2: Alt başlıkta beklentiyi doğru bir şekilde yönetiyoruz. */}
        <p className="text-lg text-gray-500 mt-2">
          Here are the first critical steps to start your journey towards: <strong>{role}</strong>
        </p>
      </div>
      <LearningPlan
        path={advice.career_advice.personalized_learning_path}
        userId={userId}
        initialCompletedWeeks={completedWeeks}
        onProgressUpdate={handleProgressUpdate}
      />
      <div className="text-center mt-12 mb-8">
        <button
          onClick={handleStartOver}
          className="text-sm font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-full px-4 py-2 transition-all duration-200"
        >
          Start Over & Plan a New Journey
        </button>
      </div>
    </main>
  );
  }

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4 bg-gray-50">
       <Toaster position="top-center" />
      <MultiStepUploadForm
        file={file}
        setFile={setFile}
        cvText={cvText}
        profile={profile}
        onUpload={handleUpload}
        onAnalyze={handleAnalyze}
        onGenerateAdvice={handleGenerateAdvice}
        isLoading={status === 'loading'}
      />
    </main>
  );
}