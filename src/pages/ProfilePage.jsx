import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/DashboardLayout';
import { useAuth } from '../context/AuthContext';
import {
  User,
  Mail,
  GraduationCap,
  Calendar,
  BookOpen,
  Zap,
  Flame,
  CheckCircle2,
  Edit3,
  Save,
  X,
  Sparkles,
  Award,
  Clock,
  Settings as SettingsIcon,
  AlertCircle,
  Info,
  RefreshCw,
  ArrowRight
} from 'lucide-react';
import {
  getUserProfile,
  updateUserProfile,
  updateUserPreferences,
  getUserSubjectsList
} from '../services/api';
import { getUserInitial } from '../utils/userUtils';

export default function ProfilePage() {
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();

  // Loading & Error States
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // User uploaded subjects for preference dropdown
  const [userSubjects, setUserSubjects] = useState([]);

  // 1. Authentic Profile State (Loaded from SQLite backend)
  const [profile, setProfile] = useState({
    id: user?.id || null,
    name: user?.full_name || 'Student',
    role: user?.course ? `${user.course} Student` : (user?.role || 'Student'),
    email: user?.email || '',
    course: user?.course || null,
    semester: user?.semester || null,
    is_course_set: Boolean(user?.course),
    is_semester_set: Boolean(user?.semester)
  });

  // Edit Mode state
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: user?.full_name || '',
    email: user?.email || '',
    course: user?.course || '',
    semester: user?.semester || ''
  });
  const [saveToast, setSaveToast] = useState(false);

  // 2. Learning Preferences State (Empty/placeholder default for new users)
  const [learningPrefs, setLearningPrefs] = useState({
    learningStyle: '',
    dailyGoal: '',
    preferredSubject: ''
  });
  const [prefsToast, setPrefsToast] = useState(false);

  // 3. Real Activity Stats State (Computed strictly from database for this user)
  const [stats, setStats] = useState({
    topics_completed: 0,
    topics_completed_subjects_count: 0,
    topics_subtext: 'No subjects yet',
    quizzes_completed: 0,
    average_score: null,
    quizzes_subtext: 'No quizzes taken yet',
    current_streak: 0,
    longest_streak: 0,
    streak_subtext: 'No streak yet',
    has_personal_best: false
  });

  // Load authentic profile data and subjects from backend database
  const loadData = async () => {
    setLoading(true);
    setErrorMessage(null);

    try {
      const [profileRes, subjectsRes] = await Promise.all([
        getUserProfile(),
        getUserSubjectsList()
      ]);

      if (profileRes.success && profileRes.data) {
        const { profile: profData, learning_preferences: prefData, stats: statsData } = profileRes.data;

        // Set Profile
        if (profData) {
          setProfile({
            id: profData.id,
            name: profData.name || 'Student',
            role: profData.role || (profData.course ? `${profData.course} Student` : 'Student'),
            email: profData.email,
            course: profData.course,
            semester: profData.semester,
            is_course_set: profData.is_course_set,
            is_semester_set: profData.is_semester_set
          });

          setEditForm({
            name: profData.name || '',
            email: profData.email || '',
            course: profData.course || '',
            semester: profData.semester || ''
          });

          // Sync with AuthContext
          if (updateUser) {
            updateUser({
              full_name: profData.name,
              course: profData.course,
              semester: profData.semester,
              role: profData.role
            });
          }
        }

        // Set Learning Preferences (preserves empty strings if not chosen)
        if (prefData) {
          setLearningPrefs({
            learningStyle: prefData.learning_style || '',
            dailyGoal: prefData.daily_goal || '',
            preferredSubject: prefData.preferred_subject || ''
          });
        }

        // Set Real Database Activity Stats
        if (statsData) {
          setStats({
            topics_completed: statsData.topics_completed ?? 0,
            topics_completed_subjects_count: statsData.topics_completed_subjects_count ?? 0,
            topics_subtext: statsData.topics_subtext || 'No subjects yet',
            quizzes_completed: statsData.quizzes_completed ?? 0,
            average_score: statsData.average_score,
            quizzes_subtext: statsData.quizzes_subtext || 'No quizzes taken yet',
            current_streak: statsData.current_streak ?? 0,
            longest_streak: statsData.longest_streak ?? 0,
            streak_subtext: statsData.streak_subtext || 'No streak yet',
            has_personal_best: Boolean(statsData.has_personal_best)
          });
        }
      }

      if (subjectsRes.success && Array.isArray(subjectsRes.data)) {
        setUserSubjects(subjectsRes.data);
      }
    } catch (err) {
      setErrorMessage('Could not load profile statistics from server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Handle Edit Profile Actions
  const handleStartEdit = () => {
    setEditForm({
      name: profile.name || '',
      email: profile.email || '',
      course: profile.course || '',
      semester: profile.semester || ''
    });
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setEditForm({
      name: profile.name || '',
      email: profile.email || '',
      course: profile.course || '',
      semester: profile.semester || ''
    });
    setIsEditing(false);
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    setErrorMessage(null);

    const res = await updateUserProfile({
      full_name: editForm.name,
      course: editForm.course || null,
      semester: editForm.semester || null
    });

    setSavingProfile(false);

    if (res.success && res.data) {
      const { profile: updatedProf, stats: updatedStats } = res.data;
      setProfile({
        id: updatedProf.id,
        name: updatedProf.name,
        role: updatedProf.role,
        email: updatedProf.email,
        course: updatedProf.course,
        semester: updatedProf.semester,
        is_course_set: updatedProf.is_course_set,
        is_semester_set: updatedProf.is_semester_set
      });

      if (updatedStats) {
        setStats(prev => ({ ...prev, ...updatedStats }));
      }

      // Update globally in AuthContext
      if (updateUser) {
        updateUser({
          full_name: updatedProf.name,
          course: updatedProf.course,
          semester: updatedProf.semester,
          role: updatedProf.role
        });
      }

      setIsEditing(false);
      setSaveToast(true);
      setTimeout(() => setSaveToast(false), 3500);
    } else {
      setErrorMessage(res.error || 'Failed to save profile changes.');
    }
  };

  // Handle Preferences Save (persisted to DB in SQLite)
  const handleSavePrefs = async (e) => {
    e.preventDefault();
    setSavingPrefs(true);
    setErrorMessage(null);

    const res = await updateUserPreferences({
      learning_style: learningPrefs.learningStyle || null,
      daily_goal: learningPrefs.dailyGoal || null,
      preferred_subject: learningPrefs.preferredSubject || null
    });

    setSavingPrefs(false);

    if (res.success && res.data) {
      const { learning_preferences: updatedPrefs } = res.data;
      if (updatedPrefs) {
        setLearningPrefs({
          learningStyle: updatedPrefs.learning_style || '',
          dailyGoal: updatedPrefs.daily_goal || '',
          preferredSubject: updatedPrefs.preferred_subject || ''
        });
      }
      setPrefsToast(true);
      setTimeout(() => setPrefsToast(false), 3500);
    } else {
      setErrorMessage(res.error || 'Failed to save learning preferences.');
    }
  };

  const isProfileComplete = profile.course && profile.semester;

  return (
    <DashboardLayout>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        {/* Toast Notification: Profile Saved */}
        {saveToast && (
          <div className="card" style={{
            background: '#ecfdf5',
            border: '1px solid #a7f3d0',
            color: '#065f46',
            padding: '0.85rem 1.25rem',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <CheckCircle2 size={18} color="#10b981" />
            <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>Profile updated and saved to database!</span>
          </div>
        )}

        {/* Toast Notification: Preferences Saved */}
        {prefsToast && (
          <div className="card" style={{
            background: '#ecfdf5',
            border: '1px solid #a7f3d0',
            color: '#065f46',
            padding: '0.85rem 1.25rem',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <CheckCircle2 size={18} color="#10b981" />
            <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>Learning preferences saved successfully to database!</span>
          </div>
        )}

        {/* Error Notification */}
        {errorMessage && (
          <div className="card" style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#991b1b',
            padding: '0.85rem 1.25rem',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <AlertCircle size={18} color="#ef4444" />
            <span style={{ fontSize: '0.88rem', fontWeight: 600 }}>{errorMessage}</span>
          </div>
        )}

        {/* Page Header */}
        <div className="ai-page-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.3rem' }}>
              <h1 style={{ fontSize: '1.65rem', fontWeight: 800 }}>My Profile</h1>
              <span className="badge badge-primary">
                <User size={13} />
                <span>Student</span>
              </span>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
              Manage your student profile and learning preferences.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.6rem' }}>
            <button
              onClick={loadData}
              disabled={loading}
              className="btn btn-secondary btn-sm"
              title="Refresh statistics from database"
            >
              <RefreshCw size={15} className={loading ? 'spin-anim' : ''} />
              <span>Refresh Stats</span>
            </button>
            <button
              onClick={() => navigate('/settings')}
              className="btn btn-secondary btn-sm"
            >
              <SettingsIcon size={15} />
              <span>Go to Settings</span>
            </button>
          </div>
        </div>

        {/* ===================================================================
            1. REAL STATS CARDS (CONNECTED TO ACTUAL DATABASE USER ACTIVITY)
            =================================================================== */}
        <div className="profile-stats-grid">
          {/* Card 1: Topics Completed */}
          <div className="profile-stat-card">
            <div className="profile-stat-icon" style={{ backgroundColor: '#eef2ff', color: '#4f46e5' }}>
              <BookOpen size={22} />
            </div>
            <div className="profile-stat-info">
              <h4>Topics Completed</h4>
              <div className="stat-value">{stats.topics_completed}</div>
              <div className="stat-sub">{stats.topics_subtext}</div>
            </div>
          </div>

          {/* Card 2: Quizzes Completed */}
          <div className="profile-stat-card">
            <div className="profile-stat-icon" style={{ backgroundColor: '#f5f3ff', color: '#7c3aed' }}>
              <Zap size={22} />
            </div>
            <div className="profile-stat-info">
              <h4>Quizzes Completed</h4>
              <div className="stat-value">{stats.quizzes_completed}</div>
              <div className="stat-sub">{stats.quizzes_subtext}</div>
            </div>
          </div>

          {/* Card 3: Study Streak */}
          <div className="profile-stat-card">
            <div className="profile-stat-icon" style={{ backgroundColor: '#fffbeb', color: '#d97706' }}>
              <Flame size={22} />
            </div>
            <div className="profile-stat-info">
              <h4>Study Streak</h4>
              <div className="stat-value">{stats.current_streak} {stats.current_streak === 1 ? 'Day' : 'Days'}</div>
              <div className="stat-sub">
                {stats.has_personal_best ? stats.streak_subtext : 'Start studying to build a streak'}
              </div>
            </div>
          </div>
        </div>

        {/* Profile Completion Prompt (If course or semester not set) */}
        {!isProfileComplete && !isEditing && (
          <div style={{
            background: 'linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%)',
            border: '1px solid #a7f3d0',
            borderRadius: 'var(--radius-md)',
            padding: '1rem 1.25rem',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ background: '#10b981', color: 'white', padding: '0.4rem', borderRadius: '50%', display: 'flex' }}>
                <GraduationCap size={18} />
              </div>
              <div>
                <h5 style={{ margin: 0, fontSize: '0.92rem', fontWeight: 700, color: '#065f46' }}>
                  Complete your student profile
                </h5>
                <p style={{ margin: '0.2rem 0 0', fontSize: '0.82rem', color: '#047857' }}>
                  Set your degree/course and academic semester to unlock personalized recommendations.
                </p>
              </div>
            </div>
            <button
              onClick={handleStartEdit}
              className="btn btn-primary btn-sm"
              style={{ whiteSpace: 'nowrap' }}
            >
              <span>Set Degree & Sem</span>
              <ArrowRight size={14} />
            </button>
          </div>
        )}

        {/* ===================================================================
            2. MAIN PROFILE CARD (AUTHENTIC DATA + SHARED AVATAR INITIAL)
            =================================================================== */}
        <div className="profile-hero-card">
          <div className="profile-header-row">
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              {/* Shared Avatar Initial: Header & Profile match 100% */}
              <div className="profile-avatar-circle" title={profile.name}>
                {getUserInitial({ full_name: profile.name, email: profile.email })}
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                  <h2 style={{ fontSize: '1.45rem', fontWeight: 800, margin: 0 }}>{profile.name}</h2>
                  <span className="badge badge-primary">
                    {profile.course ? `${profile.course} Student` : (profile.role || 'Student')}
                  </span>
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginTop: '0.2rem' }}>
                  {profile.email} • {profile.course ? profile.course : <span style={{ color: 'var(--text-muted)' }}>Course Not set</span>} ({profile.semester ? profile.semester : <span style={{ color: 'var(--text-muted)' }}>Semester Not set</span>})
                </p>
              </div>
            </div>

            {!isEditing && (
              <button
                onClick={handleStartEdit}
                className="btn btn-outline btn-sm"
              >
                <Edit3 size={15} />
                <span>Edit Profile</span>
              </button>
            )}
          </div>

          {/* View Mode vs Edit Mode */}
          {!isEditing ? (
            <div className="profile-info-grid">
              <div className="profile-info-item">
                <div className="profile-info-label">Full Name</div>
                <div className="profile-info-val">{profile.name}</div>
              </div>

              <div className="profile-info-item">
                <div className="profile-info-label">Email Address</div>
                <div className="profile-info-val">{profile.email}</div>
              </div>

              <div className="profile-info-item">
                <div className="profile-info-label">Degree / Course</div>
                <div className="profile-info-val">
                  {profile.course ? (
                    profile.course
                  ) : (
                    <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      Not set — <button onClick={handleStartEdit} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', padding: 0, fontWeight: 600 }}>Set course</button>
                    </span>
                  )}
                </div>
              </div>

              <div className="profile-info-item">
                <div className="profile-info-label">Academic Semester</div>
                <div className="profile-info-val">
                  {profile.semester ? (
                    profile.semester
                  ) : (
                    <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                      Not set — <button onClick={handleStartEdit} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', padding: 0, fontWeight: 600 }}>Set semester</button>
                    </span>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSaveProfile}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '1.5rem' }}>
                <div className="form-group">
                  <label className="form-label">Full Name</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    style={{ paddingLeft: '1rem' }}
                    value={editForm.name}
                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                    placeholder="e.g. Alex Johnson"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Email Address (Read-only)</label>
                  <input
                    type="email"
                    disabled
                    className="form-input"
                    style={{ paddingLeft: '1rem', backgroundColor: '#f8fafc', color: 'var(--text-muted)', cursor: 'not-allowed' }}
                    value={editForm.email}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Degree / Course</label>
                  <select
                    className="form-input"
                    style={{ paddingLeft: '1rem', cursor: 'pointer' }}
                    value={editForm.course}
                    onChange={(e) => setEditForm({ ...editForm, course: e.target.value })}
                  >
                    <option value="">-- Select Degree / Course --</option>
                    <option value="B.Tech CSE">B.Tech CSE</option>
                    <option value="B.Tech IT">B.Tech IT</option>
                    <option value="B.Tech ECE">B.Tech ECE</option>
                    <option value="B.Tech ME">B.Tech ME</option>
                    <option value="B.Tech Civil">B.Tech Civil</option>
                    <option value="B.E.">B.E.</option>
                    <option value="BCA">BCA</option>
                    <option value="MCA">MCA</option>
                    <option value="M.Tech">M.Tech</option>
                    <option value="B.Sc CS">B.Sc CS</option>
                    <option value="Other">Other</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Academic Semester</label>
                  <select
                    className="form-input"
                    style={{ paddingLeft: '1rem', cursor: 'pointer' }}
                    value={editForm.semester}
                    onChange={(e) => setEditForm({ ...editForm, semester: e.target.value })}
                  >
                    <option value="">-- Select Academic Semester --</option>
                    <option value="1st Semester">1st Semester</option>
                    <option value="2nd Semester">2nd Semester</option>
                    <option value="3rd Semester">3rd Semester</option>
                    <option value="4th Semester">4th Semester</option>
                    <option value="5th Semester">5th Semester</option>
                    <option value="6th Semester">6th Semester</option>
                    <option value="7th Semester">7th Semester</option>
                    <option value="8th Semester">8th Semester</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  disabled={savingProfile}
                  className="btn btn-secondary btn-sm"
                >
                  <X size={15} />
                  <span>Cancel</span>
                </button>
                <button
                  type="submit"
                  disabled={savingProfile}
                  className="btn btn-primary btn-sm"
                >
                  <Save size={15} />
                  <span>{savingProfile ? 'Saving...' : 'Save Changes'}</span>
                </button>
              </div>
            </form>
          )}
        </div>

        {/* ===================================================================
            3. LEARNING PREFERENCES (PERSISTED IN DATABASE, REAL USER SUBJECTS)
            =================================================================== */}
        <div className="settings-section-card">
          <div className="settings-section-header">
            <Sparkles size={20} color="var(--primary)" />
            <div>
              <h3>Learning Preferences</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                Personalize how EduMind AI tailors suggestions and explanations for you.
              </p>
            </div>
          </div>

          <form onSubmit={handleSavePrefs}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '1.5rem' }}>
              {/* Option 1: Preferred Learning Style */}
              <div className="form-group">
                <label className="form-label">Preferred Learning Style</label>
                <select
                  className="form-input"
                  style={{ paddingLeft: '1rem', cursor: 'pointer' }}
                  value={learningPrefs.learningStyle}
                  onChange={(e) => setLearningPrefs({ ...learningPrefs, learningStyle: e.target.value })}
                >
                  <option value="">Select your learning style</option>
                  <option value="Concept-based">Concept-based</option>
                  <option value="Problem-solving">Problem-solving</option>
                  <option value="Visual / Diagrams">Visual / Diagrams</option>
                  <option value="Exam Revision Notes">Exam Revision Notes</option>
                </select>
              </div>

              {/* Option 2: Daily Study Goal */}
              <div className="form-group">
                <label className="form-label">Daily Study Goal</label>
                <select
                  className="form-input"
                  style={{ paddingLeft: '1rem', cursor: 'pointer' }}
                  value={learningPrefs.dailyGoal}
                  onChange={(e) => setLearningPrefs({ ...learningPrefs, dailyGoal: e.target.value })}
                >
                  <option value="">Select study goal</option>
                  <option value="30 mins">30 mins</option>
                  <option value="1 hour">1 hour</option>
                  <option value="2 hours">2 hours</option>
                  <option value="3 hours">3 hours</option>
                  <option value="4+ hours">4+ hours</option>
                </select>
              </div>

              {/* Option 3: Preferred Subjects (From uploaded user subjects) */}
              <div className="form-group">
                <label className="form-label">Preferred Subject</label>
                <select
                  className="form-input"
                  style={{ paddingLeft: '1rem', cursor: 'pointer' }}
                  value={learningPrefs.preferredSubject}
                  onChange={(e) => setLearningPrefs({ ...learningPrefs, preferredSubject: e.target.value })}
                >
                  {userSubjects.length > 0 ? (
                    <>
                      <option value="">Select preferred subject</option>
                      {userSubjects.map((sub) => (
                        <option key={sub.id} value={sub.name}>
                          {sub.name} {sub.code ? `(${sub.code})` : ''}
                        </option>
                      ))}
                    </>
                  ) : (
                    <option value="" disabled>
                      Upload material to add subjects
                    </option>
                  )}
                </select>
                {userSubjects.length === 0 && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.35rem' }}>
                    Upload syllabus notes in <button type="button" onClick={() => navigate('/materials')} style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}>Materials</button> to add subjects.
                  </span>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="submit"
                disabled={savingPrefs}
                className="btn btn-primary btn-sm"
              >
                <Save size={15} />
                <span>{savingPrefs ? 'Saving...' : 'Save Preferences'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </DashboardLayout>
  );
}
