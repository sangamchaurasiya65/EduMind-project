import { startStudySession, heartbeatStudySession, stopStudySession } from './api';

let activeSessionId = null;
let activeSubjectId = null;
let heartbeatInterval = null;
let lastUserActivityTime = Date.now();
const IDLE_TIMEOUT_MS = 2 * 60 * 1000; // 2 minutes idle limit
const HEARTBEAT_INTERVAL_MS = 30 * 1000; // 30 seconds interval

// Track real user interactions to distinguish active study from idle abandonment
function recordActivity() {
  lastUserActivityTime = Date.now();
}

if (typeof window !== 'undefined') {
  ['mousemove', 'keydown', 'touchstart', 'scroll', 'click'].forEach((event) => {
    window.addEventListener(event, recordActivity, { passive: true });
  });

  // Stop counting when tab is hidden, refresh timestamp on visible
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
      lastUserActivityTime = Date.now();
    }
  });

  // Finalize active session on window close
  window.addEventListener('beforeunload', () => {
    if (activeSessionId) {
      stopStudySession(activeSessionId);
    }
  });
}

/**
 * Starts a real-time study tracking session on the backend.
 * 
 * @param {string|null} subjectId - Associated subject code or slug (optional)
 * @returns {Promise<number|null>} - Active session ID
 */
export async function beginStudySession(subjectId = null) {
  // If already tracking the same subject, retain active session
  if (activeSessionId && activeSubjectId === subjectId) {
    return activeSessionId;
  }

  // If transitioning from a previous subject, finalize it first
  if (activeSessionId) {
    await endStudySession();
  }

  try {
    const res = await startStudySession(subjectId);
    if (res.success && res.data) {
      activeSessionId = res.data.id;
      activeSubjectId = subjectId;
      lastUserActivityTime = Date.now();

      if (heartbeatInterval) clearInterval(heartbeatInterval);

      // Send heartbeat every 30 seconds while tab is visible and user active (< 2 min idle)
      heartbeatInterval = setInterval(async () => {
        // Tab must be visible
        if (document.visibilityState !== 'visible') {
          return;
        }

        // User must not be idle (> 2 min)
        const isIdle = Date.now() - lastUserActivityTime > IDLE_TIMEOUT_MS;
        if (isIdle) {
          return;
        }

        if (activeSessionId) {
          await heartbeatStudySession(activeSessionId, 30);
        }
      }, HEARTBEAT_INTERVAL_MS);

      return activeSessionId;
    }
  } catch (err) {
    console.warn('Study tracker error:', err);
  }
  return null;
}

/**
 * Finalizes and stops the currently active study session.
 */
export async function endStudySession() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
    heartbeatInterval = null;
  }
  if (activeSessionId) {
    const idToStop = activeSessionId;
    activeSessionId = null;
    activeSubjectId = null;
    try {
      await stopStudySession(idToStop);
    } catch {
      // Ignore network errors during session cleanup
    }
  }
}

/**
 * Checks if a study session is actively running.
 */
export function isCurrentlyStudying() {
  return Boolean(activeSessionId);
}

export default {
  beginStudySession,
  endStudySession,
  isCurrentlyStudying
};
