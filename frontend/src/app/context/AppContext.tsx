"use client";

import { createContext, useContext, useState, ReactNode, Dispatch, SetStateAction } from 'react';

interface AppContextType {
  role: string;
  setRole: Dispatch<SetStateAction<string>>;
  level: string;
  setLevel: Dispatch<SetStateAction<string>>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [role, setRole] = useState<string>("");
  const [level, setLevel] = useState<string>("");

  const value = { role, setRole, level, setLevel };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};