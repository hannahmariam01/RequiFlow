/**
 * Generates user stories from a given requirement using the Groq API.
 * Attempts to use the Groq API if GROQ_API_KEY is present,
 * and falls back to a rule-based mock generator if not present or on error.
 * 
 * @param {string} requirement - The input requirement text
 * @returns {Promise<string[]>} Array of user stories
 */
export async function generateUserStories(requirement) {
  const apiKey = process.env.GROQ_API_KEY;

  if (!apiKey) {
    console.warn('No GROQ_API_KEY found in environment. Using rule-based fallback generator.');
    return generateMockUserStories(requirement);
  }

  try {
    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        messages: [
          {
            role: "user",
            content: `You are an expert product owner and business analyst. Convert the following software requirement into a list of high-quality user stories.
Requirement: "${requirement}"

Each user story MUST follow the exact template:
"As a [user], I want [feature], so that [benefit]"

Do not write any introduction, markdown headings, bullet points (* or -), or numbering (1, 2, 3). Just write each user story on a new line.`
          }
        ],
        temperature: 0.3
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error?.message || `HTTP ${response.status}`);
    }

    const data = await response.json();
    const text = data.choices[0].message.content;

    const stories = text
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0)
      // strip leading numbers or bullet marks if the model disobeyed instructions
      .map(line => line.replace(/^[\d\-*\.\s]+/, '').trim());

    if (stories.length === 0) {
      throw new Error('Groq API response did not yield any stories.');
    }

    return stories;
  } catch (error) {
    console.error('Error generating user stories via Groq API:', error.message);
    console.warn('Falling back to rule-based mock generator.');
    return generateMockUserStories(requirement);
  }
}

/**
 * Local fallback rule-based generator for user stories.
 * 
 * @param {string} requirement 
 * @returns {string[]}
 */
function generateMockUserStories(requirement) {
  const reqLower = requirement.toLowerCase();
  const stories = [];

  if (reqLower.includes('login') || reqLower.includes('sign in') || reqLower.includes('auth') || reqLower.includes('register')) {
    stories.push(
      "As a user, I want to log in securely with my email and password, so that I can access my private account dashboard.",
      "As a new visitor, I want to register for a new account, so that I can save my preferences and progress.",
      "As a registered user, I want to reset my password via a secure link, so that I can regain access if I forget it."
    );
  }

  if (reqLower.includes('cart') || reqLower.includes('checkout') || reqLower.includes('buy') || reqLower.includes('shop')) {
    stories.push(
      "As a customer, I want to add items to my shopping cart, so that I can purchase them all at once.",
      "As a buyer, I want to view the summary of my cart contents, so that I can verify my items and prices before checkout.",
      "As a shopper, I want to complete my purchase using a credit card, so that I can securely order the items in my cart."
    );
  }

  if (reqLower.includes('search') || reqLower.includes('filter') || reqLower.includes('find')) {
    stories.push(
      "As a visitor, I want to search for items using a keyword search bar, so that I can quickly find products matching my interest.",
      "As a shopper, I want to filter search results by price range and rating, so that I can see the most relevant options."
    );
  }

  if (reqLower.includes('profile') || reqLower.includes('settings') || reqLower.includes('account')) {
    stories.push(
      "As a user, I want to update my profile picture and personal details, so that my account information is accurate.",
      "As an account owner, I want to change my email notification preferences, so that I only receive relevant updates."
    );
  }

  if (reqLower.includes('admin') || reqLower.includes('dashboard') || reqLower.includes('manage')) {
    stories.push(
      "As an administrator, I want to view a dashboard with system usage statistics, so that I can monitor server health and user activity.",
      "As a manager, I want to deactivate inactive user accounts, so that we can maintain security compliance."
    );
  }

  // If no keywords matched, or to provide context-specific stories, build from the requirement text
  if (stories.length === 0) {
    const topic = requirement.trim().replace(/\.$/, '');
    stories.push(
      `As a user, I want to use ${topic}, so that I can achieve my goals efficiently.`,
      `As a system operator, I want to monitor ${topic}, so that I can ensure high performance and availability.`
    );
  }

  return stories;
}
