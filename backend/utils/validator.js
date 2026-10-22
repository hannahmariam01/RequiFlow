/**
 * Validates whether a given user story matches the template format:
 * "As a [user], I want [feature], so that [benefit]"
 * 
 * @param {string} storyText - The raw user story text
 * @returns {object} { isValid: boolean, reason?: string, user?: string, feature?: string, benefit?: string }
 */
export function validateUserStory(storyText) {
  if (!storyText || typeof storyText !== 'string') {
    return { isValid: false, reason: 'Story must be a non-empty string' };
  }

  // Regex matches: "As a/an [role], I want [feature], so that [benefit]"
  // The comma before "so that" is made optional to be resilient to minor variations.
  const regex = /^As an?\s+(.+?),\s*I want\s+(.+?)(?:,\s*|\s+)so that\s+(.+)$/i;
  
  const trimmed = storyText.trim().replace(/^["']|["']$/g, ''); // strip wrapping quotes if any
  const match = trimmed.match(regex);

  if (!match) {
    return {
      isValid: false,
      reason: 'Must match template: "As a [user], I want [feature], so that [benefit]"'
    };
  }

  const [_, user, feature, benefit] = match;

  if (!user.trim() || !feature.trim() || !benefit.trim()) {
    return {
      isValid: false,
      reason: 'User, feature, and benefit parts cannot be empty'
    };
  }

  return {
    isValid: true,
    user: user.trim(),
    feature: feature.trim(),
    benefit: benefit.trim()
  };
}
