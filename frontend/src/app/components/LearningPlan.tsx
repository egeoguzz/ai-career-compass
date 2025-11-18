'use client'

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion'; 

interface Resource {
  title: string;
  url: string;
}

interface Week {
  week: number;
  topic: string;
  learning_objectives: string[];
  project_idea: string;
  resources: Resource[];
}

interface LearningPlanProps {
  path: Week[] | undefined | null;
  userId: string;
  initialCompletedWeeks: number[];
  onProgressUpdate: (newCompletedWeeks: number[]) => void;
}

const WeekAccordion = ({ week, isCompleted, onToggle, isOpen, onOpen }: any) => {
  return (
    <motion.div
      layout
      initial={{ borderRadius: 12 }}
      className={`shadow-sm transition-all duration-300 overflow-hidden ${isCompleted ? 'bg-green-100/60' : 'bg-white hover:shadow-lg'}`}
    >
      <motion.header
        layout
        className="flex items-center justify-between cursor-pointer p-4 md:p-5"
        onClick={onOpen}
      >
        <div className="flex items-center gap-4">
          <motion.div 
            className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${isCompleted ? 'bg-green-500' : 'bg-blue-500'}`}
          >
            <p className="text-white font-bold">{week.week}</p>
          </motion.div>
          <h3 className={`text-lg font-semibold ${isCompleted ? 'text-gray-500 line-through' : 'text-gray-900'}`}>
            {week.topic}
          </h3>
        </div>
        <input
          type="checkbox"
          checked={isCompleted}
          onChange={onToggle}
          onClick={(e) => e.stopPropagation()} // Header'ın tıklanmasını engelle
          className="h-6 w-6 rounded-md border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
        />
      </motion.header>

      <AnimatePresence>
        {isOpen && !isCompleted && (
          <motion.section
            key="content"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="px-4 md:px-5 pb-5"
          >
            <div className="border-t pt-4 space-y-5">
              <div>
                <p className="font-semibold text-gray-700">🎯 Learning Objectives:</p>
                <ul className="list-disc list-inside mt-2 text-gray-600 space-y-1">
                  {week.learning_objectives.map((obj: string, i: number) => <li key={i}>{obj}</li>)}
                </ul>
              </div>

              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="font-semibold text-blue-800">💡 Suggested Project:</p>
                <p className="mt-1 text-blue-900">{week.project_idea}</p>
              </div>

              {week.resources && week.resources.length > 0 && (
                <div className="border-t pt-4">
                  <p className="font-semibold text-gray-700">📚 Recommended Resources:</p>
                  <ul className="list-none mt-2 space-y-2">
                    {week.resources.map((res: Resource, i: number) => (
                      <li key={i}>
                        <a href={res.url} target="_blank" rel="noopener noreferrer" className="block bg-gray-100 p-3 rounded-md hover:bg-indigo-50 transition-colors">
                          <p className="text-indigo-600 font-semibold hover:underline">{res.title}</p>
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </motion.section>
        )}
      </AnimatePresence>
    </motion.div>
  );
};


// --- Ana LearningPlan Component'i ---
export default function LearningPlan({ path, initialCompletedWeeks, onProgressUpdate }: LearningPlanProps) {
  const [completedWeeks, setCompletedWeeks] = useState(initialCompletedWeeks);
  const [openWeek, setOpenWeek] = useState<number | null>(path && path.length > 0 ? path[0].week : null);

  useEffect(() => { setCompletedWeeks(initialCompletedWeeks) }, [initialCompletedWeeks]);

  const handleWeekToggle = (weekNumber: number) => {
    const newCompletedWeeks = completedWeeks.includes(weekNumber)
      ? completedWeeks.filter(w => w !== weekNumber)
      : [...completedWeeks, weekNumber];
    setCompletedWeeks(newCompletedWeeks);
    onProgressUpdate(newCompletedWeeks);
  };

  if (!path || path.length === 0) {
    return <p className="text-center text-gray-500 mt-10">Your learning plan is being generated...</p>;
  }

  const progressPercentage = (completedWeeks.length / path.length) * 100;

  return (
    // Adım 3: Merkezleme (mx-auto)
    <div className="space-y-6 mt-8 w-full max-w-3xl mx-auto">
      {/* Adım 2: İlerleme Çubuğu */}
      <div>
        <div className="flex justify-between mb-1">
          <span className="text-base font-medium text-blue-700">Progress</span>
          <span className="text-sm font-medium text-blue-700">{Math.round(progressPercentage)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div className="bg-blue-600 h-2.5 rounded-full transition-all duration-500" style={{ width: `${progressPercentage}%` }}></div>
        </div>
      </div>
      
      {/* Adım 2: Akordiyon Yapısı */}
      <div className="space-y-4">
        {path.map((week) => (
          <WeekAccordion
            key={week.week}
            week={week}
            isCompleted={completedWeeks.includes(week.week)}
            isOpen={openWeek === week.week}
            onToggle={() => handleWeekToggle(week.week)}
            onOpen={() => setOpenWeek(openWeek === week.week ? null : week.week)}
          />
        ))}
      </div>
    </div>
  );
}