# Profile Management Guide

**Manage Multiple Board Calibrations with Ease!**

---

## 🎯 Overview

The **Profile Management System** allows you to:
- Save multiple board configurations with different calibrations
- Switch between boards instantly (e.g., tournament board vs. travel board)
- Store piece dimensions for each board (for future gripper integration)
- Create, edit, duplicate, rename, and delete profiles

---

## 📁 What is a Profile?

A **profile** contains:
- **Board Settings**:
  - Files & Ranks (e.g., 8x8 standard chess)
  - Physical dimensions (width & height in mm)
  - **Calibration** (Origin X & Y - the machine coordinates for A1 center)
  - Default feedrate
- **Piece Dimensions** (for future gripper):
  - Height, base diameter, and grip angle for each piece type
  - Stored but not yet used until gripper is installed

---

## 🚀 Quick Start

### **Switching Profiles**

**Method 1: Toolbar Dropdown**
1. Look at the top toolbar - you'll see "Profile: [Current Profile Name]"
2. Click the dropdown to see all saved profiles
3. Select a different profile
4. Confirm the switch
5. Done! The board configuration is now loaded

**Method 2: Profile Manager**
1. Click **Settings** button
2. Click **📁 Manage Profiles**
3. Select a profile from the list
4. Click **✓ Activate**
5. The profile is now active

---

## 📝 Profile Manager

Access via: **Settings → 📁 Manage Profiles**

### **Main Window Features:**

```
┌─────────────────────────────────┐
│ 📁 Board Profiles               │
├─────────────────────────────────┤
│ Active Profile: My Board 400mm  │
├─────────────────────────────────┤
│ Saved Profiles:                 │
│ ┌─────────────────────────────┐ │
│ │ My Board 400mm ★ (Active)   │ │
│ │ Travel Board 320mm          │ │
│ │ Tournament Board            │ │
│ │ Compact Board               │ │
│ └─────────────────────────────┘ │
│                                 │
│ [✓ Activate] [✏ Edit] [📋 Dup]│
│ [✏ Rename] [🗑 Delete] [➕ New]│
└─────────────────────────────────┘
```

### **Actions:**

| Button | Description |
|--------|-------------|
| **✓ Activate** | Make selected profile the active one |
| **✏ Edit** | Open editor to change board/piece settings |
| **📋 Duplicate** | Create a copy of the selected profile |
| **✏ Rename** | Change the profile's name |
| **🗑 Delete** | Remove the profile (cannot delete active) |
| **➕ New Profile** | Create a brand new profile from scratch |

**Pro Tip:** Double-click a profile to activate it instantly!

---

## 🔧 Creating & Editing Profiles

### **Create a New Profile**

1. Open Profile Manager
2. Click **➕ New Profile**
3. Enter a name (e.g., "Living Room Board")
4. Click OK
5. The profile is created with default settings
6. Click **✏ Edit** to customize it

### **Edit a Profile**

1. Select the profile in the list
2. Click **✏ Edit**
3. You'll see two tabs:

#### **Board Settings Tab:**
```
Files (columns):         8
Ranks (rows):           8
Board Width (mm):       400.0
Board Height (mm):      400.0
Origin X - A1 center:   120.5
Origin Y - A1 center:   85.3
Default Feedrate:       2000
```

#### **Piece Settings Tab:**
```
King:
  Height (mm):          95
  Base Diameter (mm):   38
  Grip Angle (°):       90

Queen:
  Height (mm):          85
  Base Diameter (mm):   35
  Grip Angle (°):       85

[... and so on for all pieces ...]
```

4. Make your changes
5. Click **Save Changes**

---

## 🎓 Common Workflows

### **Scenario 1: Setting Up Multiple Boards**

You have two boards: a full-size tournament board and a compact travel board.

1. **Create profiles:**
   - Profile Manager → ➕ New Profile → "Tournament Board 400mm"
   - Profile Manager → ➕ New Profile → "Travel Board 320mm"

2. **Calibrate Tournament Board:**
   - Switch to "Tournament Board 400mm" profile
   - Home the machine
   - Place tournament board under gantry
   - Jog to A1 center
   - Click **📍 Set Current Position as A1**
   - Done! This calibration is saved to this profile

3. **Calibrate Travel Board:**
   - Switch to "Travel Board 320mm" profile
   - Remove tournament board, place travel board
   - Jog to A1 center
   - Click **📍 Set Current Position as A1**
   - Done! This calibration is saved to this profile

4. **Switching Between Boards:**
   - Just swap the physical board
   - Select the corresponding profile from dropdown
   - The machine now knows the correct coordinates!

### **Scenario 2: Duplicating a Profile**

You want to create a new profile similar to an existing one.

1. Profile Manager
2. Select the profile you want to copy
3. Click **📋 Duplicate**
4. Enter new name: "Tournament Board (Copy)"
5. Click **✏ Edit** to make changes
6. Adjust settings as needed

### **Scenario 3: Different Piece Sets**

You have different piece sets with different sizes.

1. Create profiles for each set:
   - "Staunton Standard Set"
   - "Travel Pieces Small"
   - "Luxury Weighted Set"

2. Edit each profile's **Piece Settings** tab
3. Measure and enter the dimensions for each set
4. When the gripper is installed, it will use these dimensions automatically!

---

## 💾 How Profiles Are Saved

Profiles are stored in: `config/settings.yaml`

**Example structure:**
```yaml
profiles:
  active: Tournament Board 400mm
  saved:
    - name: Tournament Board 400mm
      board:
        files: 8
        ranks: 8
        width_mm: 400.0
        height_mm: 400.0
        origin_x_mm: 120.5
        origin_y_mm: 85.3
        feedrate_mm_min: 2000
      pieces:
        king:
          height_mm: 95
          base_diameter_mm: 38
          grip_angle: 90
        # ... etc

    - name: Travel Board 320mm
      board:
        files: 8
        ranks: 8
        width_mm: 320.0
        height_mm: 320.0
        origin_x_mm: 65.2
        origin_y_mm: 42.8
        feedrate_mm_min: 2000
      pieces:
        # ... etc
```

---

## 🔄 Calibration Workflow with Profiles

**Old Way (Single Board):**
- Calibrate once
- If board moves or you use different board, recalibrate
- Previous calibration is lost

**New Way (Multi-Profile):**
1. Create a profile for each board
2. Calibrate each profile once
3. Switch between profiles as needed
4. **All calibrations are preserved!**

**Example:**
```
Morning: Tournament board
  → Select "Tournament Board 400mm" profile
  → Machine uses calibration: X=120.5, Y=85.3

Afternoon: Travel board
  → Select "Travel Board 320mm" profile
  → Machine uses calibration: X=65.2, Y=42.8

Never need to recalibrate unless board physically moves!
```

---

## ⚙️ Advanced: Piece Settings Explained

These settings are for **future gripper integration**.

### **Height (mm)**
- Measured from board surface to top of piece
- Used to determine how high to lift before moving
- Example: King = 95mm, Pawn = 50mm

### **Base Diameter (mm)**
- Diameter of the piece at the base
- Determines gripper claw opening width
- Example: King = 38mm, Pawn = 28mm

### **Grip Angle (°)**
- Servo angle for optimal grip strength
- Different pieces need different grip pressure
- Range: 0° (fully open) to 180° (fully closed)
- Example: Heavy King = 90°, Light Pawn = 70°

**Note:** These values are stored in each profile but won't be used until you install a gripper. They're ready for when you upgrade your hardware!

---

## 🐛 Troubleshooting

### **"Cannot delete active profile"**
- You're trying to delete the currently active profile
- **Solution:** Switch to a different profile first, then delete

### **"Profile name already exists"**
- A profile with that name is already saved
- **Solution:** Choose a different name or rename the existing one

### **Board moved after calibration**
- The board was bumped or repositioned
- **Solution:** Recalibrate the active profile (it will update the existing calibration)

### **Switched profiles but wrong coordinates**
- The profile's calibration is outdated
- **Solution:** With that profile active, recalibrate using the calibration button

---

## 🎉 Benefits of Profile System

✅ **Multiple Boards:** Switch between different chessboards instantly
✅ **Preserved Calibrations:** Never lose your calibration data
✅ **Future-Proof:** Piece dimensions ready for gripper upgrade
✅ **Easy Management:** Intuitive UI for all operations
✅ **Quick Switching:** Dropdown in main toolbar for fast changes
✅ **Backup & Restore:** Profiles saved in YAML - easy to backup

---

## 📊 Profile Lifecycle

```
┌─────────────┐
│   CREATE    │ Create new profile or duplicate existing
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    EDIT     │ Set board dimensions, calibration, piece sizes
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  ACTIVATE   │ Make it the active profile
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  CALIBRATE  │ Use "Set Current Position as A1" button
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    USE      │ Click squares, run moves - uses profile settings
└──────┬──────┘
       │
       ├──────┐
       │      ▼
       │  ┌─────────────┐
       │  │   SWITCH    │ Switch to different profile
       │  └──────┬──────┘
       │         │
       │         ▼
       │  ┌─────────────┐
       │  │  ACTIVATE   │ Different profile is now active
       │  │   OTHER     │
       │  └──────┬──────┘
       │         │
       └─────────┘
```

---

## 📚 Examples

### **Example 1: Chess Club with 3 Boards**

**Setup:**
```
Profiles created:
1. "Main Board - Tournament"    (400x400mm, Origin: 120.0, 85.0)
2. "Practice Board - Classroom" (400x400mm, Origin: 310.5, 42.3)
3. "Demo Board - Small"         (320x320mm, Origin: 200.1, 150.7)
```

**Usage:**
- Monday: Teaching in classroom → Select "Practice Board - Classroom"
- Wednesday: Tournament → Select "Main Board - Tournament"
- Friday: Demo for kids → Select "Demo Board - Small"

**All calibrations are preserved. No need to recalibrate unless boards physically move!**

### **Example 2: Home User with Seasonal Setups**

**Profiles:**
```
1. "Living Room Board" (Regular 400mm board, Standard pieces)
2. "Outdoor Board"     (Weatherproof 450mm board, Larger pieces)
3. "Travel Board"      (Compact 320mm board, Magnetic pieces)
```

**Piece settings differ:**
- Living Room: Standard Staunton (King: 95mm tall, 38mm base)
- Outdoor: Large pieces (King: 120mm tall, 50mm base)
- Travel: Small pieces (King: 70mm tall, 28mm base)

**When gripper is installed, it automatically adjusts grip based on active profile!**

---

## 🎯 Best Practices

1. **Name Profiles Descriptively**
   - Good: "Tournament Board 400mm - Staunton Set"
   - Bad: "Board1", "Test", "Untitled"

2. **Calibrate Immediately After Creating**
   - Create profile → Edit dimensions → Activate → Calibrate
   - Ensures profile is ready to use

3. **Duplicate Before Experimenting**
   - Testing new settings? Duplicate first
   - Keeps original safe

4. **Keep Profiles for Each Physical Board**
   - Even if dimensions are same, calibrations differ
   - Each board has unique positioning quirks

5. **Document Piece Dimensions Now**
   - Even if gripper isn't installed yet
   - Measure and record while pieces are available
   - Future-you will thank you!

6. **Backup settings.yaml Regularly**
   - Contains all your hard-won calibrations
   - Simple file copy to USB or cloud

---

**🎉 You're now a Profile Management expert! Happy chess moving!**

_Generated by Claude Code - 2025-01-18_
