-- =====================================================
-- Chess Mover Machine Integration for TacticsQuest
-- =====================================================
-- Adds support for physical board synchronization
-- Restricted to user: davidljones88@yahoo.com

-- Add column to track which games should sync to physical board
ALTER TABLE public.games
ADD COLUMN IF NOT EXISTS sync_to_chess_mover BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS chess_mover_user_id UUID REFERENCES auth.users(id),
ADD COLUMN IF NOT EXISTS last_synced_move_index INTEGER DEFAULT 0;

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_games_chess_mover_sync
ON public.games(sync_to_chess_mover, chess_mover_user_id)
WHERE sync_to_chess_mover = true;

-- Function to check if user is authorized for chess mover
CREATE OR REPLACE FUNCTION public.is_chess_mover_authorized(user_id UUID)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  user_email TEXT;
BEGIN
  -- Get user email
  SELECT email INTO user_email
  FROM auth.users
  WHERE id = user_id;

  -- Check if it's the authorized email
  RETURN user_email = 'davidljones88@yahoo.com';
END$$;

-- Function to enable chess mover sync for a game
CREATE OR REPLACE FUNCTION public.enable_chess_mover_sync(
  p_game_id UUID,
  p_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Check authorization
  IF NOT public.is_chess_mover_authorized(p_user_id) THEN
    RAISE EXCEPTION 'User not authorized for Chess Mover integration';
  END IF;

  -- Check if user is a player in the game
  IF NOT EXISTS (
    SELECT 1 FROM public.games
    WHERE id = p_game_id
    AND (player_white = p_user_id OR player_black = p_user_id)
  ) THEN
    RAISE EXCEPTION 'User is not a player in this game';
  END IF;

  -- Enable sync
  UPDATE public.games
  SET
    sync_to_chess_mover = true,
    chess_mover_user_id = p_user_id,
    last_synced_move_index = 0
  WHERE id = p_game_id;

  RETURN true;
END$$;

-- Function to disable chess mover sync
CREATE OR REPLACE FUNCTION public.disable_chess_mover_sync(
  p_game_id UUID,
  p_user_id UUID
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Check authorization
  IF NOT public.is_chess_mover_authorized(p_user_id) THEN
    RAISE EXCEPTION 'User not authorized for Chess Mover integration';
  END IF;

  -- Disable sync
  UPDATE public.games
  SET
    sync_to_chess_mover = false,
    chess_mover_user_id = NULL
  WHERE id = p_game_id
  AND chess_mover_user_id = p_user_id;

  RETURN true;
END$$;

-- Function to get games pending sync for chess mover
CREATE OR REPLACE FUNCTION public.get_chess_mover_pending_games(p_user_id UUID)
RETURNS TABLE (
  game_id UUID,
  player_white UUID,
  player_black UUID,
  white_username TEXT,
  black_username TEXT,
  fen TEXT,
  moves JSONB,
  last_synced_move_index INTEGER,
  total_moves INTEGER,
  status TEXT,
  time_control TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Check authorization
  IF NOT public.is_chess_mover_authorized(p_user_id) THEN
    RAISE EXCEPTION 'User not authorized for Chess Mover integration';
  END IF;

  RETURN QUERY
  SELECT
    g.id as game_id,
    g.player_white,
    g.player_black,
    g.white_username,
    g.black_username,
    g.fen,
    g.moves,
    g.last_synced_move_index,
    jsonb_array_length(g.moves) as total_moves,
    g.status,
    g.time_control
  FROM public.games g
  WHERE g.sync_to_chess_mover = true
    AND g.chess_mover_user_id = p_user_id
    AND g.status = 'active'
    AND jsonb_array_length(g.moves) > g.last_synced_move_index
  ORDER BY g.updated_at DESC;
END$$;

-- Function to mark moves as synced
CREATE OR REPLACE FUNCTION public.mark_chess_mover_synced(
  p_game_id UUID,
  p_user_id UUID,
  p_move_index INTEGER
)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Check authorization
  IF NOT public.is_chess_mover_authorized(p_user_id) THEN
    RAISE EXCEPTION 'User not authorized for Chess Mover integration';
  END IF;

  -- Update last synced index
  UPDATE public.games
  SET last_synced_move_index = p_move_index
  WHERE id = p_game_id
    AND chess_mover_user_id = p_user_id;

  RETURN true;
END$$;

-- Add to realtime publication for live updates
DO $$
BEGIN
  -- Games table should already be in realtime from main schema
  -- This ensures chess mover updates are pushed in realtime
  NULL;
END$$;

-- =====================================================
-- Usage Instructions
-- =====================================================
--
-- To enable chess mover sync for a game:
--   SELECT public.enable_chess_mover_sync(
--     '<game_id>',
--     auth.uid()
--   );
--
-- To get pending games:
--   SELECT * FROM public.get_chess_mover_pending_games(auth.uid());
--
-- To mark moves as synced:
--   SELECT public.mark_chess_mover_synced(
--     '<game_id>',
--     auth.uid(),
--     5  -- move index
--   );
--
-- To disable sync:
--   SELECT public.disable_chess_mover_sync(
--     '<game_id>',
--     auth.uid()
--   );
--
-- =====================================================
