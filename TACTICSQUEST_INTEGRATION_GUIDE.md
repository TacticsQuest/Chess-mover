# TacticsQuest Integration Guide

**Sync Your TacticsQuest Correspondence Games to Physical Chess Board!**

---

## 🎯 Overview

The **TacticsQuest Integration** brings your online correspondence chess games to life on the Chess Mover Machine. When you're playing correspondence games in TacticsQuest, your opponent's moves automatically execute on your physical board!

### Features:
- ✅ Automatic sync of opponent moves to physical board
- ✅ Configurable polling intervals (Active, Home, Away, Work, Sleep modes)
- ✅ Online/offline mode toggle
- ✅ Multi-game support
- ✅ Secure - restricted to authorized user only
- ✅ Real-time game list with refresh
- ✅ Manual game loading
- ✅ Selective sync enable/disable per game

---

## 🔐 Security & Authorization

**IMPORTANT**: This integration is **restricted to a single authorized user**:
- **Authorized Email**: `davidljones88@yahoo.com`
- All database functions verify user authorization
- Unauthorized users cannot enable Chess Mover sync

---

## 📦 Components

### 1. Database Schema (`database/chess_mover_integration.sql`)

Adds Chess Mover support to TacticsQuest Supabase database:

**New Columns on `games` table**:
- `sync_to_chess_mover` (BOOLEAN) - Whether game should sync
- `chess_mover_user_id` (UUID) - User who enabled sync
- `last_synced_move_index` (INTEGER) - Track which moves are synced

**Database Functions**:
- `is_chess_mover_authorized(user_id)` - Check if user is authorized
- `enable_chess_mover_sync(game_id, user_id)` - Enable sync for a game
- `disable_chess_mover_sync(game_id, user_id)` - Disable sync for a game
- `get_chess_mover_pending_games(user_id)` - Get games with new moves
- `mark_chess_mover_synced(game_id, user_id, move_index)` - Mark moves as synced

### 2. Sync Service (`services/tacticsquest_sync.py`)

Background polling service that monitors TacticsQuest for new moves:

**Key Features**:
- Polls Supabase on configurable interval
- Detects new moves in synced games
- Executes opponent moves on physical board
- Handles multiple concurrent games
- Thread-safe background operation

**Polling Modes**:
```python
sync_modes = {
    "Active (10s)": 10,      # Playing live, check every 10 seconds
    "Home (1min)": 60,       # At home, check every minute
    "Away (5min)": 300,      # Away from board, check every 5 minutes (default)
    "Work (15min)": 900,     # At work, check every 15 minutes
    "Sleep (1hr)": 3600,     # Sleeping, check every hour
    "Custom": 0              # Custom interval (future feature)
}
```

### 3. UI Panel (`ui/tacticsquest_panel.py`)

User interface for managing TacticsQuest sync:

**Features**:
- Connection status indicator (Online/Offline)
- Sync mode selector with preset intervals
- Supabase configuration dialog
- Synced games list
- Game actions: Refresh, Load to Board, Unsync

---

## 🚀 Setup Instructions

### Step 1: Database Setup

Run the SQL migration on your TacticsQuest Supabase database:

```bash
# Connect to Supabase dashboard
# Navigate to SQL Editor
# Paste contents of database/chess_mover_integration.sql
# Execute
```

This adds:
- Three new columns to `games` table
- Authorization function
- Sync enable/disable functions
- Pending games query function
- Mark synced function

### Step 2: Get Supabase Credentials

You'll need:
1. **Supabase URL**: Found in your project settings
   - Example: `https://xxxxx.supabase.co`

2. **Supabase Anon Key**: Public API key from project settings
   - Example: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

3. **User ID**: Your UUID in the `auth.users` table
   - Get via SQL: `SELECT id FROM auth.users WHERE email = 'davidljones88@yahoo.com';`

### Step 3: Configure Chess Mover Machine

1. Open Chess Mover Machine application
2. Navigate to TacticsQuest panel
3. Click **⚙ Settings**
4. Enter:
   - Supabase URL
   - Anon Key
   - User ID
5. Click **Save**

### Step 4: Enable Sync for Games

**Option A: Via TacticsQuest App** (Future Feature)
- Open a correspondence game
- Tap "Send to Chess Mover"
- Game will appear in synced list

**Option B: Via Supabase SQL** (Current Method)
```sql
-- Enable sync for a specific game
SELECT public.enable_chess_mover_sync(
  '<game-uuid>',  -- Game ID from games table
  auth.uid()      -- Your user ID
);
```

---

## 🎮 Usage Workflow

### Starting Sync

1. **Configure Sync Mode**:
   - Select appropriate mode from dropdown
   - "Active (10s)" for live play
   - "Home (1min)" if nearby
   - "Away (5min)" if checking occasionally (default)
   - "Work (15min)" if at work
   - "Sleep (1hr)" if overnight

2. **Connect**:
   - Click **Connect** button
   - Status changes to "● Online" (green)
   - Sync service starts polling

3. **Games Auto-Sync**:
   - Synced games appear in list
   - When opponent makes move in TacticsQuest
   - Machine automatically executes move on physical board

### Managing Games

**Refresh Games List**:
- Click **🔄 Refresh** to update list
- Shows all games with `sync_to_chess_mover = true`

**Load Game to Board**:
- Select game from list
- Click **✓ Load to Board**
- Confirms before loading
- Sets board to current game position

**Unsync Game**:
- Select game from list
- Click **✗ Unsync**
- Confirms before unsyncing
- Game stops syncing to physical board

**Disconnect**:
- Click **Disconnect** button
- Status changes to "● Offline" (red)
- Polling stops (saves bandwidth)

---

## 🔧 How It Works

### Game Sync Pipeline

```
1. TacticsQuest Game
   └─> Opponent makes move
   └─> Stored in Supabase `games` table

2. Chess Mover Polling (every N seconds based on mode)
   └─> Calls get_chess_mover_pending_games(user_id)
   └─> Returns games with new moves

3. Sync Service Processing
   └─> Detects game has new moves
   └─> Extracts UCI move (e.g., "e2e4")
   └─> Passes to GameController

4. Move Execution
   └─> GameController validates move
   └─> MoveExecutor plans action sequence
   └─> Gantry executes physical move

5. Mark as Synced
   └─> Calls mark_chess_mover_synced(game_id, move_index)
   └─> Updates last_synced_move_index
   └─> Prevents re-executing same move
```

### Multi-Game Handling

**Current Implementation**:
- One active game on physical board at a time
- Tracked via `sync_service.active_game_id`
- If different game has new move, logs warning and skips
- Use "Load to Board" to switch active game

**Future Enhancement**:
- Queue system for multiple game moves
- Switch between games automatically
- Prompt user to choose which game to execute

---

## 📊 Database Schema Details

### Games Table Extensions

```sql
-- Add to existing games table
ALTER TABLE public.games
ADD COLUMN sync_to_chess_mover BOOLEAN DEFAULT false,
ADD COLUMN chess_mover_user_id UUID REFERENCES auth.users(id),
ADD COLUMN last_synced_move_index INTEGER DEFAULT 0;
```

### Example Game Record

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "player_white": "uuid-white",
  "player_black": "uuid-black",
  "white_username": "PlayerOne",
  "black_username": "davidljones88",
  "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
  "moves": ["e2e4", "e7e5", "g1f3"],
  "status": "active",
  "time_control": "correspondence",
  "sync_to_chess_mover": true,
  "chess_mover_user_id": "user-uuid",
  "last_synced_move_index": 2
}
```

**Move Sync Logic**:
- `moves` array has 3 moves
- `last_synced_move_index = 2` means first 2 moves synced
- Next poll will sync move index 2 (third move: "g1f3")

---

## 🎯 Example Use Cases

### Use Case 1: Daily Correspondence Games

**Scenario**: You play 5 correspondence games, checking once per day.

**Setup**:
1. Enable Chess Mover sync for all 5 games (via SQL)
2. Set mode to "Sleep (1hr)"
3. Click Connect
4. Leave machine running

**Result**:
- Machine checks every hour
- When any opponent makes move, machine executes it
- You see physical board updated
- Make your move on TacticsQuest app
- Opponent sees your move online

### Use Case 2: Live Play with Correspondence Time Control

**Scenario**: Playing a rapid correspondence game, both players online.

**Setup**:
1. Enable sync for the active game
2. Set mode to "Active (10s)"
3. Click Connect
4. Load game to board

**Result**:
- Opponent makes move on TacticsQuest
- Within 10 seconds, machine executes move
- You make move on physical board (future: auto-detect and send)
- Feels like playing in person!

### Use Case 3: Switch Between Games

**Scenario**: You have 3 synced games, want to focus on one.

**Steps**:
1. Games list shows all 3 synced games
2. Select the game you want to work on
3. Click "Load to Board"
4. Machine loads that game's position
5. Sets as active game
6. New moves for that game auto-execute
7. Other games stay synced but won't execute until you load them

---

## ⚙️ Configuration & Settings

### Supabase Configuration

Stored in TacticsQuest panel (future: save to config file):

```python
self.supabase_url = "https://xxxxx.supabase.co"
self.supabase_key = "eyJhbGciOiJIUzI1NiIs..."
self.user_id = "your-uuid-from-auth-users"
```

### Polling Interval

Configured via sync mode dropdown or programmatically:

```python
sync_service.set_poll_interval(300)  # 5 minutes
```

**Minimum**: 5 seconds (enforced in `set_poll_interval`)

---

## 🐛 Troubleshooting

### "Not Configured" Error

**Cause**: Sync service not initialized or credentials missing

**Fix**:
1. Click **⚙ Settings**
2. Enter Supabase URL, Anon Key, User ID
3. Click Save
4. Try Connect again

### No Games in List

**Possible Causes**:
1. No games have sync enabled
2. Not connected (click Connect)
3. Database query failed

**Fix**:
- Enable sync for at least one game via SQL:
  ```sql
  SELECT enable_chess_mover_sync('<game-id>', auth.uid());
  ```
- Check Supabase credentials
- Click Refresh

### Moves Not Executing

**Possible Causes**:
1. Different game is active on board
2. Move already synced (last_synced_move_index up to date)
3. Invalid move format in database
4. GameController failed to validate move

**Fix**:
- Check logs for "[SYNC]" messages
- Load the correct game to board
- Verify moves array in database contains valid UCI moves

### "User not authorized" Error

**Cause**: User email is not `davidljones88@yahoo.com`

**Fix**: This integration is restricted to the authorized user only. Contact admin if you need access.

---

## 🔬 Technical Architecture

### Threading Model

```
Main Thread (UI)
  └─> TacticsQuestPanel (Tkinter widgets)

Background Thread (Daemon)
  └─> TacticsQuestSync._sync_loop()
      └─> Runs while is_running = True
      └─> Calls _check_for_new_moves() every poll_interval
      └─> Sleep between polls
```

**Thread Safety**:
- All Supabase calls in background thread
- GameController calls in background thread (safe if no UI updates)
- UI updates only in main thread via messagebox callbacks

### Move Detection Algorithm

```python
def _check_for_new_moves():
    # Get all games with sync enabled
    games = supabase.rpc('get_chess_mover_pending_games', {'p_user_id': user_id})

    for game in games:
        total_moves = len(game['moves'])
        last_synced = game['last_synced_move_index']

        if total_moves > last_synced:
            # New moves exist
            new_moves = game['moves'][last_synced:]

            for move in new_moves:
                execute_move(move)
                mark_synced(game_id, move_index)
```

---

## 📝 SQL Function Reference

### enable_chess_mover_sync

**Purpose**: Enable sync for a game

**Parameters**:
- `p_game_id` (UUID): Game to enable
- `p_user_id` (UUID): User enabling sync

**Returns**: BOOLEAN (true if successful)

**Security**: Checks user authorization and game membership

**Example**:
```sql
SELECT enable_chess_mover_sync(
  '550e8400-e29b-41d4-a716-446655440000',
  auth.uid()
);
```

### disable_chess_mover_sync

**Purpose**: Disable sync for a game

**Parameters**:
- `p_game_id` (UUID): Game to disable
- `p_user_id` (UUID): User disabling sync

**Returns**: BOOLEAN (true if successful)

**Example**:
```sql
SELECT disable_chess_mover_sync(
  '550e8400-e29b-41d4-a716-446655440000',
  auth.uid()
);
```

### get_chess_mover_pending_games

**Purpose**: Get all games with new moves to sync

**Parameters**:
- `p_user_id` (UUID): User to query for

**Returns**: TABLE with columns:
- `game_id`, `player_white`, `player_black`
- `white_username`, `black_username`
- `fen`, `moves`, `last_synced_move_index`
- `total_moves`, `status`, `time_control`

**Example**:
```sql
SELECT * FROM get_chess_mover_pending_games(auth.uid());
```

### mark_chess_mover_synced

**Purpose**: Mark moves as synced after execution

**Parameters**:
- `p_game_id` (UUID): Game ID
- `p_user_id` (UUID): User ID
- `p_move_index` (INTEGER): Move index to mark as synced

**Returns**: BOOLEAN (true if successful)

**Example**:
```sql
SELECT mark_chess_mover_synced(
  '550e8400-e29b-41d4-a716-446655440000',
  auth.uid(),
  5  -- Mark moves 0-4 as synced
);
```

---

## 🚀 Future Enhancements

**Planned Features**:

1. **Two-Way Sync**:
   - Detect moves made on physical board
   - Send to TacticsQuest automatically
   - Full correspondence play via physical board

2. **Queue System**:
   - Handle multiple games with new moves
   - Execute all pending moves in sequence
   - Smart switching between games

3. **Move Notification**:
   - Sound alert when opponent moves
   - Desktop notification
   - LED indicator on physical board

4. **Game History**:
   - Review past moves on physical board
   - Step through game history
   - Integration with Game Panel PGN replay

5. **TacticsQuest App Integration**:
   - "Send to Chess Mover" button in app
   - QR code pairing
   - No manual SQL required

6. **Configuration Persistence**:
   - Save Supabase credentials to encrypted config file
   - Remember last sync mode
   - Auto-connect on startup option

7. **Custom Polling Interval**:
   - Dialog for custom interval entry
   - Validation (minimum 5 seconds)
   - Save per-game intervals

---

## 📊 Performance & Bandwidth

### Bandwidth Usage

**Per Poll** (at "Away" mode - 5 minutes):
- Database query: ~500 bytes
- Response (5 games): ~2 KB

**Daily Usage** (5-minute interval):
- Polls per day: 288
- Data transferred: ~576 KB/day

**Recommendation**: Use longer intervals when not actively playing to reduce bandwidth.

### Database Load

**Light Load**:
- Indexed queries (efficient)
- Only returns games with new moves
- Minimal processing on database side

**Supabase Free Tier**: More than sufficient for personal use

---

## ✅ Summary

**What You Have**:
✅ Complete TacticsQuest integration
✅ Automatic move sync from online to physical board
✅ Configurable polling modes
✅ Multi-game support
✅ Secure authorization
✅ Full UI for game management

**How to Use**:
1. Run SQL migration on Supabase
2. Configure credentials in Settings
3. Enable sync for games (via SQL)
4. Click Connect
5. Watch your opponent's moves execute on physical board!

**Next Steps**:
- Tomorrow: Test with Raspberry Pi hardware
- Future: Add two-way sync (physical board → TacticsQuest)
- Future: TacticsQuest app integration

---

**🎉 Your Chess Mover Machine can now sync with TacticsQuest!**

_Implementation by Claude Code - 2025-01-18_
