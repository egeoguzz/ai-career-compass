'use client'

import { useState } from "react"
import { useRouter } from "next/navigation"

export default function OnboardingPage() {
  const router = useRouter()
  const [role, setRole] = useState("")
  const [level, setLevel] = useState("")

  const handleSubmit = () => {
  if (!role || !level) {
    alert("Please fill in both fields.")
    return
  }

  localStorage.setItem("user_role", role)
  localStorage.setItem("user_level", level)

  router.push("/upload")
}

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-4 bg-white text-gray-900">
      <h1 className="text-3xl font-bold">What is your dream role?</h1>
      <input
        type="text"
        placeholder="e.g. AI Engineer at Google"
        value={role}
        onChange={(e) => setRole(e.target.value)}
        className="p-2 border rounded w-full max-w-md"
      />

      <h2 className="text-xl mt-4">What is your current experience level?</h2>
      <select
        value={level}
        onChange={(e) => setLevel(e.target.value)}
        className="p-2 border rounded w-full max-w-md"
      >
        <option value="">Select...</option>
        <option value="student">Student</option>
        <option value="junior">Recent Graduate / Junior</option>
        <option value="mid">1-3 Years of Experience</option>
        <option value="senior">5+ Years of Experience</option>
      </select>

      <button
        className="mt-6 bg-black text-white px-4 py-2 rounded"
        onClick={handleSubmit}
      >
        Continue
      </button>
    </main>
  )
}
