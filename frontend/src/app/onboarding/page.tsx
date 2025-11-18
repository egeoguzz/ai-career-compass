"use client";

import { useState } from "react"; 
import { useRouter } from "next/navigation";
import { Toaster, toast } from 'react-hot-toast';
import { useAppContext } from "../context/AppContext";
import { validateRole } from "../services/api";

export default function OnboardingPage() {
  const router = useRouter();
  const { role, setRole, level, setLevel } = useAppContext();
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    if (!role.trim() || !level) {
      toast.error("Please fill in both your dream role and experience level.");
      return;
    }

    setIsLoading(true);
    const toastId = toast.loading("Validating your target role...");

    try {
      const result = await validateRole(role);

      if (result.is_in_scope) {
        toast.success("Great! That role is a perfect fit.", { id: toastId });
        router.push("/upload");
      } else {
        toast.error(`Unsupported Role: ${result.reason}`, { 
          id: toastId, 
          duration: 6000 
        });
      }
    } catch (error: any) {
      toast.error(`An error occurred: ${error.message}`, { id: toastId });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-4 bg-gray-50 text-gray-900">
      <Toaster position="top-center" />
      <div className="w-full max-w-md bg-white p-8 rounded-lg shadow-md text-center">
        
        <h1 className="text-2xl md:text-3xl font-bold">What is Your Dream Role?</h1>
        <p className="text-gray-600 mt-2 mb-6">Let's set your career target to personalize your roadmap.</p>

        <div className="text-left">
          <label htmlFor="role-input" className="block text-sm font-medium text-gray-700 mb-1">
            Target Role
          </label>
          <input
            id="role-input"
            type="text"
            placeholder="e.g., Senior AI Engineer at Google"
            value={role}
            onChange={(e) => setRole(e.target.value)} 
            className="p-3 border rounded-lg w-full focus:ring-2 focus:ring-blue-500 transition"
            disabled={isLoading} 
          />
          <p className="text-xs text-gray-500 mt-1 pl-1">
            Expertise in digital tech roles like Software Engineer, Data Scientist, etc.
          </p>
        </div>

        <div className="text-left mt-4">
          <label htmlFor="level-select" className="block text-sm font-medium text-gray-700 mb-1">
            Current Experience Level
          </label>
          <select
            id="level-select"
            value={level}
            onChange={(e) => setLevel(e.target.value)} 
            className="p-3 border rounded-lg w-full focus:ring-2 focus:ring-blue-500 transition"
            disabled={isLoading} 
          >
            <option value="" disabled>Select your level...</option>
            <option value="student">Student / Aspiring</option>
            <option value="junior">Recent Graduate / Junior (0-1 years)</option>
            <option value="mid">Mid-level (1-4 years)</option>
            <option value="senior">Senior (5+ years)</option>
          </select>
        </div>
        
        <button
          className="mt-8 w-full bg-blue-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
          onClick={handleSubmit}
          disabled={isLoading} 
        >
          {isLoading ? "Validating..." : "Continue"}
        </button>
      </div>
    </main>
  );
}