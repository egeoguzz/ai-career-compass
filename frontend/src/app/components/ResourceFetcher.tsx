'use client'

import { useState } from "react" 

interface Recommendation {
  recommended_title: string;
  recommended_url: string;
  reason: string;
}

export default function ResourceFetcher({ topic }: { topic: string }) {
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasFetched, setHasFetched] = useState(false);

  const handleFetchResources = async () => {
    setLoading(true)
    setError(null)
    setHasFetched(true); // Butona basıldığını işaretle

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/suggest_resources`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ learning_objective: topic }),
      })

      if (!res.ok) {
        throw new Error(`Failed to fetch resources for ${topic}`)
      }

      const data = await res.json()
      setRecommendation(data.recommendation || null)

    } catch (err) {
      console.error("Resource fetch error:", err)
      setError("Could not fetch resources.")
    } finally {
      setLoading(false)
    }
  }

  // --- JSX (ARAYÜZ) KISMINI TAMAMEN DEĞİŞTİRİYORUZ ---

  // Eğer butona henüz basılmadıysa, sadece butonu göster
  if (!hasFetched) {
    return (
        <div className="mt-4">
            <button 
                onClick={handleFetchResources}
                className="w-full bg-blue-500 hover:bg-blue-600 text-white text-sm font-semibold py-2 px-4 rounded-md transition-colors"
            >
                📚 Find Recommended Resource
            </button>
        </div>
    )
  }

  // Butona basıldıktan sonraki durumlar (yükleniyor, hata, sonuç)
  if (loading) return <p className="text-sm text-gray-500 mt-4">🔄 Finding the best resource for "{topic}"...</p>

  if (error) return <p className="text-sm text-red-500 mt-4">Error: {error}</p>

  if (!recommendation || recommendation.recommended_title === "No specific resource found") {
    return <p className="text-sm text-gray-500 mt-4">❌ No resources found for "{topic}"</p>
  }

  // Başarılı sonuç
  return (
    <div className="mt-4 space-y-2">
      <p className="font-semibold text-sm">📚 Recommended Resource:</p>
      <div className="text-sm text-gray-800 bg-gray-50 p-3 rounded-md border">
          <a href={recommendation.recommended_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline font-bold">
            {recommendation.recommended_title}
          </a>
          <p className="mt-1 text-gray-600 italic">"{recommendation.reason}"</p>
      </div>
    </div>
  )
}