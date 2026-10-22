import express from 'express';
import { generateUserStories } from '../services/aiService.js';
import { validateUserStory } from '../utils/validator.js';

const router = express.Router();

/**
 * @route POST /api/generate-user-stories
 * @desc Generate user stories from a requirement text and validate them
 * @access Public
 */
router.post('/generate-user-stories', async (req, res) => {
  try {
    const { requirement } = req.body;

    if (!requirement || typeof requirement !== 'string' || !requirement.trim()) {
      return res.status(400).json({
        error: 'Missing or invalid "requirement" parameter in the request body. It must be a non-empty string.'
      });
    }

    // Generate user stories using AI service (with fallback)
    const rawStories = await generateUserStories(requirement.trim());

    // Validate each generated user story
    let allValid = true;
    const validationDetails = rawStories.map(story => {
      const val = validateUserStory(story);
      if (!val.isValid) {
        allValid = false;
      }
      return {
        story,
        isValid: val.isValid,
        ...(val.reason ? { reason: val.reason } : {})
      };
    });

    res.json({
      user_stories: rawStories,
      validation_result: {
        isValid: allValid,
        details: validationDetails
      }
    });

  } catch (error) {
    console.error('Error in /generate-user-stories route:', error);
    res.status(500).json({
      error: 'An internal server error occurred while generating user stories.'
    });
  }
});

export default router;
