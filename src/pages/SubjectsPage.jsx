import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import DashboardLayout from '../components/DashboardLayout';
import {
  BookOpen,
  Layers,
  BrainCircuit,
  Zap,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Lock,
  PlayCircle,
  Search,
  Sparkles,
  Bot,
  FileText,
  HelpCircle,
  Cpu,
  Calculator,
  Compass,
  Clock,
  Upload,
  RefreshCw,
  AlertCircle,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { getSubjectsProgress, getSubjectProgress, toggleSubjectTopic } from '../services/api';

export default function SubjectsPage() {
  const navigate = useNavigate();
  const { slug } = useParams();

  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState(null);
  const [expandedChapters, setExpandedChapters] = useState({});

  const toggleChapter = (chapterId) => {
    setExpandedChapters(prev => ({
      ...prev,
      [chapterId]: prev[chapterId] === false ? true : false
    }));
  };

  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState('All'); // 'All' | 'In Progress' | 'Completed' | 'Not Started'

  const handleToggleTopic = async (topicTitle, markAsDone) => {
    if (!slug) return;
    try {
      const res = await toggleSubjectTopic(slug, topicTitle, markAsDone);
      if (res.success && res.data?.subject_progress) {
        setSelectedSubject(res.data.subject_progress);
      } else {
        await loadSingleSubject(slug);
      }
    } catch {
      await loadSingleSubject(slug);
    }
  };


  // Load all user subjects on mount or when returning to main list
  useEffect(() => {
    loadSubjects();
  }, []);

  // Load specific subject details if slug parameter is present
  useEffect(() => {
    if (slug) {
      loadSingleSubject(slug);
    } else {
      setSelectedSubject(null);
    }
  }, [slug]);

  const loadSubjects = async () => {
    setLoading(true);
    setError(null);
    const res = await getSubjectsProgress();
    setLoading(false);
    if (res.success && Array.isArray(res.data)) {
      setSubjects(res.data);
    } else {
      setError(res.error || 'Failed to load subjects.');
    }
  };

  const loadSingleSubject = async (subjectSlug) => {
    setLoadingDetail(true);
    setError(null);
    const res = await getSubjectProgress(subjectSlug);
    setLoadingDetail(false);
    if (res.success && res.data) {
      setSelectedSubject(res.data);
    } else {
      setError(res.error || `Could not load details for subject "${subjectSlug}".`);
    }
  };

  // Filter and search live subjects
  const filteredSubjects = useMemo(() => {
    return subjects.filter((subject) => {
      // 1. Text Search Filter
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        (subject.name && subject.name.toLowerCase().includes(q)) ||
        (subject.code && subject.code.toLowerCase().includes(q)) ||
        (subject.description && subject.description.toLowerCase().includes(q)) ||
        (subject.current_topic && subject.current_topic.toLowerCase().includes(q));

      // 2. Category Tab Filter
      let matchesFilter = true;
      if (activeFilter === 'In Progress') {
        matchesFilter = subject.status_key === 'in-progress' || subject.status === 'In Progress';
      } else if (activeFilter === 'Completed') {
        matchesFilter = subject.status_key === 'completed' || subject.status === 'Completed';
      } else if (activeFilter === 'Not Started') {
        matchesFilter = subject.status_key === 'not-started' || subject.status === 'Not Started';
      }

      return matchesSearch && matchesFilter;
    });
  }, [subjects, searchQuery, activeFilter]);

  // Open Subject Detail View
  const handleOpenSubject = (subjectId) => {
    navigate(`/subjects/${subjectId}`);
  };

  // Back to Subject Cards List
  const handleBackToList = () => {
    navigate('/subjects');
  };

  return (
    <DashboardLayout>
      <div className="subjects-page-wrapper">
        {/* ===================================================================
            VIEW 1: SUBJECT DETAILS VIEW (When slug matches a subject)
            =================================================================== */}
        {slug ? (
          loadingDetail ? (
            <div style={{ padding: '4rem 1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              <RefreshCw size={28} className="spin-anim" style={{ margin: '0 auto 1rem', display: 'block', color: 'var(--primary)' }} />
              <p style={{ fontWeight: 600, fontSize: '1rem', margin: '0 0 0.35rem' }}>Loading subject details...</p>
            </div>
          ) : error || !selectedSubject ? (
            <div className="card" style={{ padding: '3rem 1.5rem', textAlign: 'center' }}>
              <AlertCircle size={32} style={{ color: 'var(--danger)', margin: '0 auto 0.75rem', display: 'block' }} />
              <h3>Subject Not Found</h3>
              <p style={{ color: 'var(--text-secondary)', margin: '0.5rem auto 1.25rem', maxWidth: '420px' }}>
                {error || `We couldn't find subject "${slug}" in your enrolled library.`}
              </p>
              <button onClick={handleBackToList} className="btn btn-primary btn-sm">
                Back to All Subjects
              </button>
            </div>
          ) : (
            <div className="subject-detail-view-container">
              {/* Top Navigation Back Button */}
              <button onClick={handleBackToList} className="btn btn-secondary btn-sm" style={{ marginBottom: '1.25rem' }}>
                <ArrowLeft size={16} />
                <span>Back to All Subjects</span>
              </button>

              {/* Subject Detail Hero Banner */}
              <div className="subject-detail-hero-card">
                <div className="detail-hero-main">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginBottom: '0.6rem' }}>
                    <div
                      className="brand-icon"
                      style={{
                        width: 44,
                        height: 44,
                        backgroundColor: selectedSubject.bg || '#eef2ff',
                        color: selectedSubject.color || '#4f46e5'
                      }}
                    >
                      <BookOpen size={22} />
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
                        <h1 style={{ fontSize: '1.65rem', fontWeight: 800, margin: 0 }}>{selectedSubject.name}</h1>
                        <span
                          className="badge"
                          style={{
                            backgroundColor: selectedSubject.bg || '#eef2ff',
                            color: selectedSubject.color || '#4f46e5',
                            fontSize: '0.78rem'
                          }}
                        >
                          {selectedSubject.code}
                        </span>
                      </div>
                      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '0.35rem' }}>
                        <span
                          className={`badge ${
                            selectedSubject.status_key === 'completed'
                              ? 'badge-success'
                              : selectedSubject.status_key === 'in-progress'
                              ? 'badge-primary'
                              : 'badge-secondary'
                          }`}
                          style={{ fontSize: '0.72rem' }}
                        >
                          {selectedSubject.status}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          • {selectedSubject.materials_count} {selectedSubject.materials_count === 1 ? 'Material' : 'Materials'} uploaded
                        </span>
                      </div>
                    </div>
                  </div>

                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '680px', lineHeight: '1.55' }}>
                    {selectedSubject.description}
                  </p>
                </div>

                {/* Progress Box */}
                <div className="detail-hero-progress-box">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)' }}>Subject Progress</span>
                    <span style={{ fontSize: '1.2rem', fontWeight: 800, color: selectedSubject.color || 'var(--primary)' }}>
                      {selectedSubject.progress_percent}%
                    </span>
                  </div>

                  <div className="progress-track" style={{ height: 10, background: '#e2e8f0' }}>
                    <div
                      className="progress-fill"
                      style={{
                        width: `${selectedSubject.progress_percent}%`,
                        backgroundColor: selectedSubject.color || 'var(--primary)'
                      }}
                    />
                  </div>

                  <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.4rem', display: 'block' }}>
                    Current Topic: <strong>{selectedSubject.progress_percent > 0 ? selectedSubject.current_topic : 'Not started yet'}</strong>
                  </span>
                </div>
              </div>

              {/* Course Content / Syllabus Chapters */}
              <div className="card" style={{ marginTop: '1.75rem' }}>
                <div className="section-header-compact" style={{ marginBottom: '1.25rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.2rem' }}>Course Content & Chapters</h3>
                    <p>Organized topics extracted from your uploaded study materials</p>
                  </div>
                  <span className="badge badge-primary">
                    {selectedSubject.chapters ? selectedSubject.chapters.length : 0} Chapters
                  </span>
                </div>

                {selectedSubject.chapters && selectedSubject.chapters.length > 0 ? (
                  <div className="chapters-timeline-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {selectedSubject.chapters.map((ch) => {
                      const isExpanded = expandedChapters[ch.id] !== false; // expanded by default
                      const topicsCount = ch.topics_count || (ch.topics ? ch.topics.length : 0);
                      const masteredCount = ch.topics_mastered || 0;

                      return (
                        <div
                          key={ch.id}
                          style={{
                            background: 'var(--bg-surface)',
                            border: ch.status === 'current' ? '1.5px solid var(--primary)' : '1px solid var(--border-light)',
                            borderRadius: 'var(--radius-lg)',
                            boxShadow: ch.status === 'current' ? '0 0 0 1px var(--primary-light), var(--shadow-sm)' : 'var(--shadow-sm)',
                            overflow: 'hidden',
                            transition: 'all 0.2s ease'
                          }}
                        >
                          {/* Chapter Header Row */}
                          <div
                            style={{
                              padding: '1rem 1.25rem',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              gap: '1rem',
                              backgroundColor: ch.status === 'current' ? 'var(--primary-light)' : 'var(--bg-surface)',
                              borderBottom: isExpanded && ch.topics && ch.topics.length > 0 ? '1px solid var(--border-light)' : 'none',
                              cursor: 'pointer'
                            }}
                            onClick={() => toggleChapter(ch.id)}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                              <div className="chapter-status-icon" style={{ flexShrink: 0 }}>
                                {ch.status === 'completed' && (
                                  <div className="icon-circle-comp" title="Chapter Completed">
                                    <CheckCircle2 size={19} color="#10b981" />
                                  </div>
                                )}
                                {ch.status === 'current' && (
                                  <div className="icon-circle-curr" title="Current Active Chapter">
                                    <PlayCircle size={19} color="var(--primary)" />
                                  </div>
                                )}
                                {ch.status !== 'completed' && ch.status !== 'current' && (
                                  <div className="icon-circle-lock" title="Not Started">
                                    <Clock size={17} color="var(--text-muted)" />
                                  </div>
                                )}
                              </div>

                              <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                                  <h4 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>
                                    Chapter {ch.id}: {ch.title}
                                  </h4>
                                  {ch.status === 'completed' && (
                                    <span className="badge badge-success" style={{ fontSize: '0.68rem', padding: '0.12rem 0.5rem' }}>
                                      ✓ Completed
                                    </span>
                                  )}
                                  {ch.status === 'current' && (
                                    <span className="badge badge-primary" style={{ fontSize: '0.68rem', padding: '0.12rem 0.5rem' }}>
                                      → In Progress
                                    </span>
                                  )}
                                  {ch.status !== 'completed' && ch.status !== 'current' && (
                                    <span className="badge" style={{ backgroundColor: 'var(--bg-surface-alt)', color: 'var(--text-muted)', fontSize: '0.68rem', padding: '0.12rem 0.5rem' }}>
                                      ○ Not Started
                                    </span>
                                  )}
                                </div>

                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', marginTop: '0.3rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                                    <Clock size={12} /> {ch.duration || '20 mins'}
                                  </span>
                                  {topicsCount > 0 && (
                                    <span style={{ fontWeight: 600, color: masteredCount === topicsCount ? '#059669' : 'var(--text-secondary)' }}>
                                      • {masteredCount}/{topicsCount} Topics Mastered
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  toggleChapter(ch.id);
                                }}
                                className="btn btn-outline btn-sm"
                                style={{ padding: '0.35rem 0.6rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}
                              >
                                <span style={{ fontSize: '0.75rem' }}>{isExpanded ? 'Hide Topics' : 'Show Topics'}</span>
                                {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                              </button>
                            </div>
                          </div>

                          {/* Subtopics List */}
                          {isExpanded && ch.topics && ch.topics.length > 0 && (
                            <div style={{ padding: '0.75rem 1rem 0.75rem 2rem', backgroundColor: 'var(--bg-main)' }}>
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                                {ch.topics.map((tp, tpIdx) => {
                                  const statusConfig = {
                                    mastered: {
                                      bg: '#ecfdf5',
                                      color: '#065f46',
                                      border: '#a7f3d0',
                                      label: '✓ Mastered (100%)',
                                      icon: CheckCircle2,
                                      iconColor: '#10b981'
                                    },
                                    practised: {
                                      bg: '#f0f9ff',
                                      color: '#0369a1',
                                      border: '#bae6fd',
                                      label: '⚡ Practised (50%)',
                                      icon: Zap,
                                      iconColor: '#0284c7'
                                    },
                                    reading: {
                                      bg: '#fffbeb',
                                      color: '#b45309',
                                      border: '#fde68a',
                                      label: '📖 Reading (25%)',
                                      icon: BookOpen,
                                      iconColor: '#d97706'
                                    },
                                    not_started: {
                                      bg: '#f8fafc',
                                      color: '#64748b',
                                      border: '#e2e8f0',
                                      label: '○ Not started (0%)',
                                      icon: Clock,
                                      iconColor: '#94a3b8'
                                    }
                                  };

                                  const cfg = statusConfig[tp.status] || statusConfig.not_started;
                                  const StatusIcon = cfg.icon;

                                  return (
                                    <div
                                      key={tp.id || tpIdx}
                                      style={{
                                        backgroundColor: 'var(--bg-surface)',
                                        border: '1px solid var(--border-light)',
                                        borderRadius: 'var(--radius-md)',
                                        padding: '0.75rem 1rem',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'space-between',
                                        gap: '0.85rem'
                                      }}
                                    >
                                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', flex: 1 }}>
                                        <div style={{ marginTop: '0.2rem' }}>
                                          <StatusIcon size={16} color={cfg.iconColor} />
                                        </div>
                                        <div>
                                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                                            <h5 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-main)' }}>
                                              {tp.title}
                                            </h5>
                                            <span
                                              style={{
                                                fontSize: '0.68rem',
                                                fontWeight: 700,
                                                padding: '0.1rem 0.45rem',
                                                borderRadius: '9999px',
                                                backgroundColor: cfg.bg,
                                                color: cfg.color,
                                                border: `1px solid ${cfg.border}`
                                              }}
                                            >
                                              {cfg.label}
                                            </span>
                                          </div>
                                          {tp.summary && (
                                            <p style={{ margin: '0.25rem 0 0', fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                                              {tp.summary}
                                            </p>
                                          )}
                                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '0.25rem', fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                                            <span>⏱ {tp.estimated_minutes || 15} mins study</span>
                                            {tp.quiz_attempts_count > 0 && (
                                              <span>• {tp.quiz_attempts_count} {tp.quiz_attempts_count === 1 ? 'quiz attempt' : 'quiz attempts'}</span>
                                            )}
                                            {tp.best_score !== null && tp.best_score !== undefined && (
                                              <span>• Best Score: <strong>{tp.best_score}%</strong></span>
                                            )}
                                          </div>
                                        </div>
                                      </div>

                                      {/* Action Buttons */}
                                      <div style={{ display: 'flex', gap: '0.35rem', alignItems: 'center', flexShrink: 0 }}>
                                        <button
                                          onClick={() => handleToggleTopic(tp.title, tp.status !== 'mastered')}
                                          className="btn btn-sm"
                                          style={{
                                            fontSize: '0.75rem',
                                            padding: '0.25rem 0.55rem',
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            gap: '0.3rem',
                                            backgroundColor: tp.status === 'mastered' ? '#ecfdf5' : '#ffffff',
                                            color: tp.status === 'mastered' ? '#047857' : 'var(--text-secondary)',
                                            border: tp.status === 'mastered' ? '1px solid #a7f3d0' : '1px solid var(--border-light)'
                                          }}
                                          title={tp.status === 'mastered' ? 'Mark Incomplete' : 'Mark Topic as Mastered'}
                                        >
                                          <CheckCircle2 size={12} color={tp.status === 'mastered' ? '#10b981' : '#94a3b8'} />
                                          <span>{tp.status === 'mastered' ? 'Mastered' : 'Mark Done'}</span>
                                        </button>
                                        <button
                                          onClick={() => navigate('/quizzes')}
                                          className="btn btn-outline btn-sm"
                                          style={{ fontSize: '0.75rem', padding: '0.25rem 0.55rem' }}
                                          title="Practice quiz for this topic"
                                        >
                                          <Zap size={12} />
                                          <span>Practice</span>
                                        </button>
                                        <button
                                          onClick={() => navigate('/assistant')}
                                          className="btn btn-primary btn-sm"
                                          style={{ fontSize: '0.75rem', padding: '0.25rem 0.55rem' }}
                                          title="Ask AI about this topic"
                                        >
                                          <Bot size={12} />
                                          <span>Ask AI</span>
                                        </button>
                                      </div>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{ padding: '2.5rem 1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                    <p style={{ margin: 0 }}>No chapters found for this subject. Upload syllabus notes in Materials to populate chapters!</p>
                  </div>
                )}
              </div>

              {/* Learning Resource Cards / Recommended Resources */}
              <div style={{ marginTop: '2rem' }}>
                <div className="section-header-compact" style={{ marginBottom: '1.25rem' }}>
                  <div>
                    <h3 style={{ fontSize: '1.2rem' }}>Study Actions</h3>
                    <p>Study materials and practice modules to reinforce your understanding</p>
                  </div>
                </div>

                <div className="resources-cards-grid">
                  {/* 1. Upload/Review Notes */}
                  <div className="resource-card">
                    <div className="resource-icon-box" style={{ backgroundColor: '#eef2ff', color: '#4f46e5' }}>
                      <FileText size={22} />
                    </div>
                    <h4>Course Materials</h4>
                    <p>Review uploaded documents, lecture summaries, and formula sheets.</p>
                    <button
                      onClick={() => navigate('/materials')}
                      className="btn btn-outline btn-sm"
                      style={{ width: '100%', marginTop: 'auto', justifyContent: 'center' }}
                    >
                      <span>Open Materials</span>
                    </button>
                  </div>

                  {/* 2. Practice Quiz */}
                  <div className="resource-card">
                    <div className="resource-icon-box" style={{ backgroundColor: '#ecfdf5', color: '#10b981' }}>
                      <PlayCircle size={22} />
                    </div>
                    <h4>Interactive Quiz</h4>
                    <p>Test your knowledge with AI-generated assessments from your notes.</p>
                    <button
                      onClick={() => navigate('/quizzes')}
                      className="btn btn-outline btn-sm"
                      style={{ width: '100%', marginTop: 'auto', justifyContent: 'center' }}
                    >
                      <span>Take Quiz</span>
                    </button>
                  </div>

                  {/* 3. Ask EduMind AI */}
                  <div className="resource-card" style={{ border: '1.5px solid #c7d2fe', background: 'linear-gradient(180deg, #ffffff 0%, #f5f3ff 100%)' }}>
                    <div className="resource-icon-box" style={{ backgroundColor: '#f5f3ff', color: '#7c3aed' }}>
                      <Bot size={22} />
                    </div>
                    <h4>Ask EduMind AI</h4>
                    <p>Ask doubts, get step-by-step solutions, and clarify tricky topics.</p>
                    <button
                      onClick={() => navigate('/assistant')}
                      className="btn btn-primary btn-sm"
                      style={{ width: '100%', marginTop: 'auto', justifyContent: 'center' }}
                    >
                      <Sparkles size={14} />
                      <span>Ask AI Tutor</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )
        ) : (
          /* ===================================================================
              VIEW 2: ALL SUBJECTS GRID (Loaded strictly from Database)
              =================================================================== */
          <div>
            {/* Header */}
            <div className="ai-page-header" style={{ marginBottom: '1.5rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.3rem' }}>
                  <h1 style={{ fontSize: '1.65rem', fontWeight: 800 }}>My Subjects</h1>
                  <span className="badge badge-primary">{subjects.length} Enrolled</span>
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
                  Choose a subject and continue learning with real, verified progress tracking.
                </p>
              </div>

              {subjects.length > 0 && (
                <button
                  onClick={() => navigate('/materials')}
                  className="btn btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}
                >
                  <Upload size={16} />
                  <span>Upload Material</span>
                </button>
              )}
            </div>

            {/* Loading State */}
            {loading && (
              <div style={{ padding: '4rem 1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <RefreshCw size={28} className="spin-anim" style={{ margin: '0 auto 1rem', display: 'block', color: 'var(--primary)' }} />
                <p style={{ fontWeight: 600, fontSize: '1rem', margin: '0 0 0.35rem' }}>Loading your subjects...</p>
              </div>
            )}

            {/* Error State */}
            {!loading && error && (
              <div style={{ padding: '1.25rem', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: 'var(--radius-md)', color: '#991b1b', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>{error}</span>
                <button onClick={loadSubjects} className="btn btn-secondary btn-sm">Retry</button>
              </div>
            )}

            {/* ===============================================================
                EMPTY STATE: User has zero subjects enrolled
                =============================================================== */}
            {!loading && !error && subjects.length === 0 && (
              <div
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px dashed var(--border-light)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '4rem 2rem',
                  textAlign: 'center',
                  boxShadow: 'var(--shadow-sm)',
                  marginTop: '1rem'
                }}
              >
                <div
                  style={{
                    width: 60,
                    height: 60,
                    borderRadius: '50%',
                    backgroundColor: 'var(--primary-light)',
                    color: 'var(--primary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 1.25rem'
                  }}
                >
                  <BookOpen size={30} />
                </div>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 800, margin: '0 0 0.5rem', color: 'var(--text-main)' }}>
                  Abhi koi subject nahi hai
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '480px', margin: '0 auto 1.75rem', lineHeight: 1.6 }}>
                  Study material upload karo, subject apne aap ban jayega aur aapki learning progress real activity se track hogi.
                </p>
                <button
                  onClick={() => navigate('/materials')}
                  className="btn btn-primary"
                  style={{ padding: '0.65rem 1.6rem', fontSize: '0.95rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  <Upload size={17} />
                  <span>Upload Material</span>
                </button>
              </div>
            )}

            {/* ===============================================================
                MAIN SUBJECTS CATALOG GRID (Visible only when subjects > 0)
                =============================================================== */}
            {!loading && !error && subjects.length > 0 && (
              <div>
                {/* Search Bar & Category Filters Toolbar */}
                <div className="subjects-filter-toolbar">
                  {/* Search Field */}
                  <div className="subjects-search-wrapper">
                    <Search size={18} className="search-icon-inside" />
                    <input
                      type="text"
                      className="subjects-search-input"
                      placeholder="Search subjects or topics..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    {searchQuery && (
                      <button
                        onClick={() => setSearchQuery('')}
                        className="search-clear-btn"
                        title="Clear search"
                        aria-label="Clear search"
                      >
                        ✕
                      </button>
                    )}
                  </div>

                  {/* Category Filter Buttons */}
                  <div className="subjects-category-tabs">
                    {['All', 'In Progress', 'Completed', 'Not Started'].map((filterName) => (
                      <button
                        key={filterName}
                        className={`category-tab-btn ${activeFilter === filterName ? 'tab-selected' : ''}`}
                        onClick={() => setActiveFilter(filterName)}
                      >
                        {filterName}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Subjects Grid */}
                {filteredSubjects.length > 0 ? (
                  <div className="subjects-catalog-grid">
                    {filteredSubjects.map((sub) => {
                      const isCompleted = sub.status_key === 'completed' || sub.status === 'Completed';
                      const isInProgress = sub.status_key === 'in-progress' || sub.status === 'In Progress';

                      return (
                        <div key={sub.id} className="subject-catalog-card">
                          <div>
                            {/* Top Code, Materials Count & Status */}
                            <div className="sub-card-top-row">
                              <div
                                className="sub-icon-box"
                                style={{
                                  backgroundColor: sub.bg || '#eef2ff',
                                  color: sub.color || '#4f46e5'
                                }}
                              >
                                <BookOpen size={20} />
                              </div>
                              <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                                <span
                                  className="badge"
                                  style={{
                                    backgroundColor: sub.bg || '#eef2ff',
                                    color: sub.color || '#4f46e5',
                                    fontSize: '0.72rem'
                                  }}
                                >
                                  {sub.code}
                                </span>
                                <span
                                  className={`badge ${
                                    isCompleted
                                      ? 'badge-success'
                                      : isInProgress
                                      ? 'badge-primary'
                                      : 'badge-secondary'
                                  }`}
                                  style={{ fontSize: '0.7rem' }}
                                >
                                  {sub.status}
                                </span>
                              </div>
                            </div>

                            {/* Subject Title & Description */}
                            <h3 className="sub-card-title">{sub.name}</h3>
                            <p className="sub-card-desc">{sub.description}</p>

                            {/* Progress Bar & Percentage */}
                            <div className="sub-card-progress-section">
                              <div className="sub-card-progress-labels">
                                <span>Progress</span>
                                <span style={{ fontWeight: 800, color: sub.color || 'var(--primary)' }}>
                                  {sub.progress_percent}%
                                </span>
                              </div>
                              <div className="progress-track" style={{ height: 8 }}>
                                <div
                                  className="progress-fill"
                                  style={{
                                    width: `${sub.progress_percent}%`,
                                    backgroundColor: sub.color || 'var(--primary)'
                                  }}
                                />
                              </div>
                            </div>

                            {/* Materials Count & Current Topic Meta */}
                            <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.3rem', fontSize: '0.78rem' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                                <span>Materials:</span>
                                <strong style={{ color: 'var(--text-main)' }}>
                                  {sub.materials_count} {sub.materials_count === 1 ? 'file' : 'files'}
                                </strong>
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                                <span>Current Topic:</span>
                                <strong style={{ color: sub.progress_percent > 0 ? 'var(--text-main)' : 'var(--text-muted)' }}>
                                  {sub.progress_percent > 0 ? sub.current_topic : 'Not started yet'}
                                </strong>
                              </div>
                            </div>
                          </div>

                          {/* Action Button */}
                          <div className="sub-card-footer" style={{ marginTop: '1.25rem' }}>
                            <button
                              onClick={() => handleOpenSubject(sub.id)}
                              className={`btn ${isCompleted ? 'btn-secondary' : 'btn-primary'}`}
                              style={{ width: '100%', justifyContent: 'center' }}
                            >
                              <span>{isCompleted ? 'Review Subject' : isInProgress ? 'Continue Learning' : 'Start Subject'}</span>
                              <ArrowRight size={15} />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  /* Empty Search Results */
                  <div className="card" style={{ padding: '3.5rem 2rem', textAlign: 'center', marginTop: '1.5rem' }}>
                    <div className="brand-icon" style={{ width: 52, height: 52, margin: '0 auto 1rem', backgroundColor: 'var(--bg-surface-alt)', color: 'var(--text-muted)' }}>
                      <Search size={24} />
                    </div>
                    <h3>No matching subjects found</h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '420px', margin: '0.4rem auto 1.5rem' }}>
                      No subjects match your filter "{activeFilter}" or search "{searchQuery}".
                    </p>
                    <button
                      onClick={() => { setSearchQuery(''); setActiveFilter('All'); }}
                      className="btn btn-secondary btn-sm"
                    >
                      Reset Search & Filters
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
