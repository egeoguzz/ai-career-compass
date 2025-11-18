import React from 'react';
import { ExtractedProfile } from '../types';

type MultiStepUploadFormProps = {
  file: File | null;
  setFile: (file: File | null) => void;
  cvText: string | null;
  profile: ExtractedProfile | null;
  onUpload: () => void;
  onAnalyze: () => void;
  onGenerateAdvice: () => void;
  isLoading: boolean;
};

const FileIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

export default function MultiStepUploadForm({
  file,
  setFile,
  cvText,
  profile,
  onUpload,
  onAnalyze,
  onGenerateAdvice,
  isLoading,
}: MultiStepUploadFormProps) {
  return (
    <div className="text-center w-full max-w-xl mx-auto">
      <h1 className="text-4xl font-bold text-gray-800">
        Get Your AI Career Compass
      </h1>
      <p className="text-lg text-gray-500 mt-2 mb-10">
        Upload your CV to get a personalized roadmap to your dream job.
      </p>
      
      <div className="bg-white p-6 sm:p-8 rounded-xl shadow-lg transition-all duration-300">
        
        {!cvText && (
          <>
            {!file ? (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 hover:bg-gray-50 transition-colors">
                <input
                  type="file"
                  id="cv-upload"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
                <label htmlFor="cv-upload" className="cursor-pointer">
                  <p className="text-blue-600 font-semibold">Choose a file</p>
                  <p className="text-sm text-gray-500 mt-1">or drag and drop it here</p>
                  <p className="text-xs text-gray-400 mt-4">PDF, DOCX, TXT supported</p>
                </label>
              </div>
            ) : (
              <div className="border-2 border-solid border-green-500 bg-green-50 rounded-lg p-4 text-left flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-green-600">
                    <FileIcon />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-800 truncate">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                <button 
                  onClick={() => setFile(null)} 
                  className="text-gray-500 hover:text-red-600 font-bold p-1 rounded-full transition-colors"
                  aria-label="Remove file"
                >
                  X
                </button>
              </div>
            )}

            <button
              className="mt-6 w-full bg-blue-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition-all duration-300 transform hover:scale-105"
              onClick={onUpload}
              disabled={isLoading || !file}
            >
              {isLoading ? 'Processing...' : 'Upload & Extract Text'}
            </button>
          </>
        )}

        {cvText && !profile && (
          <>
            <div className="text-left bg-gray-50 p-4 rounded-lg border border-gray-200 max-h-60 overflow-y-auto">
              <h2 className="text-sm font-semibold mb-2 text-gray-600">Extracted Text Preview:</h2>
              <p className="text-sm text-gray-800 whitespace-pre-wrap">{cvText}</p>
            </div>
            <button
              className="mt-4 w-full bg-blue-600 text-white px-4 py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition-all duration-300 transform hover:scale-105"
              onClick={onAnalyze}
              disabled={isLoading}
            >
              {isLoading ? 'Analyzing...' : 'Analyze Profile'}
            </button>
          </>
        )}

        {profile && (
          <>
            <div className="text-left p-4 bg-green-50 rounded-lg border border-green-200">
              <h2 className="text-lg font-semibold text-green-800">✅ Profile Analysis Complete!</h2>
              <p className="text-green-700 mt-1">Your profile is structured. Ready for the final step?</p>
            </div>
            <button
              className="mt-4 w-full bg-gray-900 text-white px-4 py-3 rounded-lg font-semibold hover:bg-black disabled:opacity-50 transition-all duration-300 transform hover:scale-105"
              onClick={onGenerateAdvice}
              disabled={isLoading}
            >
              {isLoading ? 'Generating...' : '✨ Generate My Career Roadmap'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}