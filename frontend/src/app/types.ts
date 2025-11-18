export interface PersonalInfo {
  name: string;
}

export interface Skill {
  name: string;
  level?: string;
}

export interface ExtractedProfile {
  personal_info: PersonalInfo;
  skills: Skill[];
  experience_years: number;
  contact_email?: string;
}

export interface CareerAdvice {
  identified_skill_gaps: string[];
  suggested_portfolio_projects: string[];
  personalized_learning_path: any[];
}

export interface CareerAdviceResponse {
  career_advice: CareerAdvice;
  role_fit_score?: number;
}

export interface AdviceRequestData {
    profile: ExtractedProfile;
    role: string;
    level: string;
}