# Chess Mover Machine - Calibration Guide

**Easy Board Calibration in 3 Simple Steps!**

---

## 🎯 Quick Calibration (Recommended Method)

### **Step 1: Home the Machine**
1. Launch the app: `python main.py`
2. Click **Connect**
3. Click **Home** button
4. Wait for homing to complete

### **Step 2: Position Over A1**
1. Place your chessboard under the gantry
2. Use the **arrow buttons** to jog the head
3. Position the laser/head exactly over the **center of square A1**
   - Use the jog distance selector (1mm, 10mm, 50mm, 100mm)
   - Fine-tune with 1mm jogging for precision

### **Step 3: Calibrate!**
1. Click **"📍 Set Current Position as A1"** button
2. Confirm in the dialog
3. Done! ✓

**That's it!** Your board is now perfectly calibrated. All click-to-move commands will be accurate.

---

## 📐 How It Works

The calibration feature:
1. Reads the current machine position from GRBL
2. Saves it as the "origin" (A1 center coordinates)
3. Updates the board configuration automatically
4. All future moves are calculated relative to this origin

**Before Calibration:**
- You had to manually measure and enter coordinates
- Prone to measurement errors
- Time-consuming

**After Calibration:**
- Instant, accurate calibration
- No manual measurements needed
- Can recalibrate anytime if board moves

---

## 🔄 Re-Calibration

**When to Recalibrate:**
- Board was bumped or moved
- You want to use a different board size
- Initial calibration seems off

**How to Recalibrate:**
Just repeat the 3 steps above! The new calibration overwrites the old one.

---

## ⚙️ Manual Calibration (Advanced)

If you prefer to manually enter coordinates:

1. Click **Settings** button
2. Enter **Origin X (A1 center, mm)** - machine X coordinate of A1's center
3. Enter **Origin Y (A1 center, mm)** - machine Y coordinate of A1's center
4. Enter **Width (mm)** - physical board width
5. Enter **Height (mm)** - physical board height
6. Click **Save**

**Note:** The quick calibration method is much easier and more accurate!

---

## 📏 Board Dimensions

You still need to enter the board dimensions in Settings:

**Standard 400mm Board:**
- Width: 400mm
- Height: 400mm
- Square size: 50mm

**Compact 320mm Board:**
- Width: 320mm
- Height: 320mm
- Square size: 40mm

**Custom Board:**
- Measure the outer edges
- Enter actual dimensions
- Square size = Width / 8

---

## ✅ Verification

**After calibration, test it:**

1. Click **Test Path** button
   - Head should visit: A1 → H1 → H8 → A8 → center → A1
2. Or manually click different squares
3. Verify head moves to square centers accurately

**If positions are slightly off:**
- Recalibrate (maybe you weren't exactly centered on A1)
- Check board dimensions in Settings
- Ensure board hasn't moved

---

## 🎓 Pro Tips

### **Better Accuracy:**
- Use the 1mm jog distance for final positioning
- Look straight down at the board (avoid parallax error)
- Mark A1 center with a small dot for reference
- Use good lighting

### **Physical Setup:**
- Ensure board is square to the gantry axes
- Tape board down so it doesn't move
- Use a flat, level surface
- Keep consistent orientation

### **Workflow:**
- Calibrate once when you first set up
- Only recalibrate if board moves
- Save different calibrations for different boards (use Settings → profiles)

---

## 🐛 Troubleshooting

### **"Could not read current position"**
- Make sure you clicked **Connect** first
- Wait for GRBL to finish homing
- Try clicking the calibrate button again

### **Head doesn't move to square centers**
- Recalibrate more carefully
- Check board Width/Height in Settings
- Verify board is flat and hasn't moved
- Try **Test Path** to see the pattern

### **Calibration saved but squares still wrong**
- Check if board dimensions match your physical board
- Make sure board orientation is correct (A1 should be bottom-left from your view)
- Verify board didn't shift during/after calibration

### **Want to reset to manual coordinates**
- Click **Settings**
- Manually enter Origin X and Y coordinates
- Click **Save**

---

## 🎯 Example Workflow

**Setting up for the first time:**

```
1. Launch app → Connect → Home
2. Place 400mm board under gantry
3. Open Settings:
   - Width: 400
   - Height: 400
   - Files: 8, Ranks: 8
   - Click Save
4. Jog to A1 center (bottom-left square)
5. Click "📍 Set Current Position as A1"
6. Click "Test Path" to verify
7. Start using! Click squares to move.
```

**Total time:** ~2 minutes! 🚀

---

## 📝 Coordinate System

```
Chess Board Layout (from above):

A8  B8  C8  D8  E8  F8  G8  H8  ← Rank 8 (top)
A7  B7  C7  D7  E7  F7  G7  H7
A6  B6  C6  D6  E6  F6  G6  H6
A5  B5  C5  D5  E5  F5  G5  H5
A4  B4  C4  D4  E4  F4  G4  H4
A3  B3  C3  D3  E3  F3  G3  H3
A2  B2  C2  D2  E2  F2  G2  H2
A1  B1  C1  D1  E1  F1  G1  H1  ← Rank 1 (bottom)
↑
File A (leftmost)

A1 = Origin (0,0 in chess coordinates)
A1 = (origin_x, origin_y) in machine coordinates
```

The calibration sets `(origin_x, origin_y)` to the current machine position.

---

**🎉 You're all set! Happy chess moving!**

_Generated by Claude Code - 2025-01-18_
