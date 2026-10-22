import express from 'express';
import { spawn } from 'child_process';
import path from 'path';

const router = express.Router();

router.post('/run-orchestrator', (req, res) => {
  const { input_text, original_requirements, user_answers } = req.body;
  const payload = { input_text, original_requirements, user_answers };
  
  const scriptPath = path.resolve('orchestrator.py');
  
  // spawn passes arguments directly to the process without shell expansion or quote stripping
  const pythonProcess = spawn('python', [scriptPath, '--json', JSON.stringify(payload)]);

  let stdoutData = '';
  let stderrData = '';

  pythonProcess.stdout.on('data', (data) => {
    stdoutData += data.toString();
  });

  pythonProcess.stderr.on('data', (data) => {
    stderrData += data.toString();
  });

  pythonProcess.on('close', (code) => {
    if (code !== 0) {
      console.error(`Orchestrator process exited with code ${code}. Stderr: ${stderrData}`);
      return res.status(500).json({ error: `Orchestrator failed with exit code ${code}`, details: stderrData });
    }

    try {
      const response = JSON.parse(stdoutData.trim());
      res.json(response);
    } catch (e) {
      console.error('Failed to parse orchestrator output:', stdoutData);
      res.status(500).json({
        error: 'Orchestrator returned invalid JSON format',
        raw: stdoutData,
        parseError: e.message
      });
    }
  });
});

export default router;
