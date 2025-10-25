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
  const [highlightedSkills, setHighlightedSkills] = useState<string[]>([])
  const [adviceJson, setAdviceJson] = useState<any>(null)
  const [editMode, setEditMode] = useState(false)

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
    const rawAdvice = data.advice

    const cleanAdvice = rawAdvice
      .replace(/```json/g, "")
      .replace(/```/g, "")
      .trim()

    const parsedAdvice = JSON.parse(cleanAdvice)
    setAdviceJson(parsedAdvice)
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

    if (data.highlighted_skills) {
      setHighlightedSkills(data.highlighted_skills)
      console.log("✨ Highlighted skills:", data.highlighted_skills)
    } else {
      setHighlightedSkills([])
    }
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
  <>
    <pre className="bg-gray-200 p-4 rounded max-w-xl overflow-x-auto text-sm">
      {JSON.stringify(profile, null, 2)}
    </pre>

    {highlightedSkills.length > 0 && (
      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-2">Highlighted Skills:</h3>
        <div className="flex flex-wrap gap-2">
          {highlightedSkills.map((skill) => (
            <span
              key={skill}
              className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm"
            >
              {skill}
            </span>
          ))}
        </div>
      </div>
    )}
  </>
)}

{adviceJson && (
  <div className="w-full max-w-2xl mt-10 space-y-4">
    <div className="flex justify-between items-center">
      <h2 className="text-xl font-bold">Career Advice (Editable)</h2>
      <button
        onClick={() => setEditMode(!editMode)}
        className="text-sm underline text-blue-600"
      >
        {editMode ? "Hide Editor" : "Edit JSON"}
      </button>
    </div>

    {editMode ? (
      <textarea
        className="w-full h-80 p-4 border rounded bg-gray-50 font-mono text-sm"
        value={JSON.stringify(adviceJson, null, 2)}
        onChange={(e) => {
          try {
            setAdviceJson(JSON.parse(e.target.value))
          } catch (err) {
            console.warn("Invalid JSON")
          }
        }}
      />
    ) : (
      <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto whitespace-pre-wrap">
        {JSON.stringify(adviceJson, null, 2)}
      </pre>
    )}

    <button
      className="bg-black text-white px-4 py-2 rounded"
      onClick={() => {
        console.log("🛠️ Updated advice:", adviceJson)
        alert("Advice updated (not re-generated)")
      }}
    >
      Save Changes
    </button>
  </div>
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

