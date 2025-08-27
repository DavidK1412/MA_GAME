-- Migration: Add belief fields to game_attempts table
-- This migration adds the belief system fields to track AI agent evaluations

-- Add belief fields for each controller
ALTER TABLE game_attempts 
ADD COLUMN IF NOT EXISTS advice_belief DECIMAL(3,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS feedback_belief DECIMAL(3,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS explain_belief DECIMAL(3,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS demonstrate_belief DECIMAL(3,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS ask_belief DECIMAL(3,2) DEFAULT 0.00;

-- Add indexes for better query performance on belief fields
CREATE INDEX IF NOT EXISTS idx_game_attempts_advice_belief ON game_attempts(advice_belief);
CREATE INDEX IF NOT EXISTS idx_game_attempts_feedback_belief ON game_attempts(feedback_belief);
CREATE INDEX IF NOT EXISTS idx_game_attempts_explain_belief ON game_attempts(explain_belief);
CREATE INDEX IF NOT EXISTS idx_game_attempts_demonstrate_belief ON game_attempts(demonstrate_belief);
CREATE INDEX IF NOT EXISTS idx_game_attempts_ask_belief ON game_attempts(ask_belief);

-- Add composite index for active attempts with beliefs
CREATE INDEX IF NOT EXISTS idx_game_attempts_active_beliefs ON game_attempts(is_active, advice_belief, feedback_belief, explain_belief, demonstrate_belief, ask_belief);

-- Add comments to document the belief fields
COMMENT ON COLUMN game_attempts.advice_belief IS 'Belief value for advice controller (0.00-1.00)';
COMMENT ON COLUMN game_attempts.feedback_belief IS 'Belief value for feedback controller (0.00-1.00)';
COMMENT ON COLUMN game_attempts.explain_belief IS 'Belief value for explain controller (0.00-1.00)';
COMMENT ON COLUMN game_attempts.demonstrate_belief IS 'Belief value for demonstrate controller (0.00-1.00)';
COMMENT ON COLUMN game_attempts.ask_belief IS 'Belief value for ask controller (0.00-1.00)';

-- Update existing records to have default belief values
UPDATE game_attempts 
SET 
    advice_belief = 0.00,
    feedback_belief = 0.00,
    explain_belief = 0.00,
    demonstrate_belief = 0.00,
    ask_belief = 0.00
WHERE advice_belief IS NULL 
   OR feedback_belief IS NULL 
   OR explain_belief IS NULL 
   OR demonstrate_belief IS NULL 
   OR ask_belief IS NULL;
