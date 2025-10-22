'use client'

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

export default function UploadPage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [text, setText] = useState("")
  const [profile, setProfile] = useState("")
  const [loading, setLoading] = useState(false)
  const [role, setRole] = useState("")
  const [level, setLevel] = useState("")

useEffect(() => {
  const savedRole = localStorage.getItem("user_role")
  const savedLevel = localStorage.getItem("user_level")

  if (!savedRole || !savedLevel) {
    router.push("/onboarding")
  }

  if (savedRole) setRole(savedRole)
  if (savedLevel) setLevel(savedLevel)
}, [])

const handleUpload = async () => {
  if (!file) return alert("Please select a file!")

  const formData = new FormData()
  formData.append("file", file)

  setLoading(true)

  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/upload_cv`, {
      method: "POST",
      body: formData,
    })

    if (!res.ok) {
      throw new Error(`❌ Server returned ${res.status}`)
    }

    const data = await res.json()
    setText(data?.text || "No text found")
  } catch (err) {
    alert("Upload failed. Check console for details.")
  } finally {
    setLoading(false)
  }
}

const handleGenerateAdvice = async () => {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/generate_advice`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        profile,
        role,
        level,
      }),
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error("❌ Server error:", errorText);
      return;
    }

    const data = await res.json();
    console.log("✅ Advice received:", data);
  } catch (err) {
    console.error("🔥 Request failed:", err);
  }
};


const handleAnalyze = async () => {
  if (!text) {
    alert("CV text is empty. Upload your CV first.")
    return
  }

  setLoading(true)

  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/analyze_profile`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cv_text: text }),
    })

    if (!res.ok) {
      throw new Error(`Server returned ${res.status}`)
    }

    const data = await res.json()
    console.log("📄 Structured profile:", data)
    const match = data.profile.match(/```json([\s\S]*?)```/)
    const jsonString = match ? match[1].trim() : data.profile

    const parsed = JSON.parse(jsonString)
    setProfile(parsed) 
  } catch (err) {
    console.error("🔥 Analyze error:", err)
    alert("Failed to analyze CV. Check console for details.")
  } finally {
    setLoading(false)
  }
}

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 p-4 bg-white text-gray-900">
      <h1 className="text-2xl font-bold">Upload Your CV (PDF or DOCX)</h1>

      <input
        type="file"
        accept=".pdf,.docx"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
        className="border p-2 rounded w-full max-w-md"
      />

      <button
        className="bg-black text-white px-4 py-2 rounded disabled:opacity-50"
        onClick={handleUpload}
        disabled={loading}
      >
        {loading ? "Uploading..." : "Upload"}
      </button>

      {text && (
        <>
          <div className="bg-gray-100 p-4 rounded w-full max-w-xl whitespace-pre-wrap">
            <h2 className="text-lg font-semibold mb-2">Extracted Text:</h2>
            <p>{text}</p>
          </div>

          <button
            className="bg-black text-white px-4 py-2 rounded"
            onClick={handleAnalyze}
          >
            Continue
          </button>
        </>
)}

{profile && (
  <pre className="bg-gray-200 p-4 rounded max-w-xl overflow-x-auto text-sm">
    {JSON.stringify(profile, null, 2)}
  </pre>
)}

{text && profile && (
  <button
    className="bg-black text-white px-4 py-2 rounded"
    onClick={handleGenerateAdvice}
  >
    Generate Career Advice
  </button>
)}

    </main>
  )
}
