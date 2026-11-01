/**
 * Shared utility functions for user profile, avatars, and time-based greetings.
 * Ensures consistent display across all pages and layouts.
 */

/**
 * Returns the uppercase first letter of the user's name or email.
 * Guarantees that Header, Profile, and other views display the exact same avatar initial.
 * Uses '?' as a neutral fallback if the user or name is missing (no hardcoded letter).
 * 
 * @param {object|null|string} user - Authenticated user object or name string
 * @returns {string} Single uppercase letter or '?'
 */
export function getUserInitial(user) {
  if (!user) return '?';
  if (typeof user === 'string') {
    const trimmed = user.trim();
    return trimmed.length > 0 ? trimmed.charAt(0).toUpperCase() : '?';
  }
  const name = user.full_name || user.fullName || user.name || user.username || '';
  if (typeof name === 'string' && name.trim().length > 0) {
    return name.trim().charAt(0).toUpperCase();
  }
  const email = user.email || '';
  if (typeof email === 'string' && email.trim().length > 0) {
    return email.trim().charAt(0).toUpperCase();
  }
  return '?';
}

/**
 * Returns a greeting string based on the current local time of day:
 * - 05:00 to 11:59: 'Good Morning'
 * - 12:00 to 16:59: 'Good Afternoon'
 * - 17:00 to 04:59: 'Good Evening'
 * 
 * @returns {string}
 */
export function getTimeBasedGreeting() {
  const currentHour = new Date().getHours();
  if (currentHour >= 5 && currentHour < 12) {
    return 'Good Morning';
  }
  if (currentHour >= 12 && currentHour < 17) {
    return 'Good Afternoon';
  }
  return 'Good Evening';
}
