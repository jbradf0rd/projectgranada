Here's the revised specification with date-based organization:

Granada Notepad: Date-Organized Sidebar Layout
Structure (RTL)
┌─────────────────────────────────────────────────────────────────────┐
│                         Top Navigation Bar                          │
├──────────────────────────────────────────┬──────────────────────────┤
│                                          │                          │
│                                          │   اليوم                  │
│           Editor Area                    │     فائدة 1533           │
│                                          │     فائدة 1420           │
│                                          │   أمس                    │
│                                          │     فائدة 0911           │
│                                          │   هذا الأسبوع            │
│                                          │     فائدة ...            │
│                                          │                          │
├──────────────────────────────────────────┴──────────────────────────┤
│                           Status Bar                                │
└─────────────────────────────────────────────────────────────────────┘
Sidebar Specifications
Width: 260px (collapsible)
Header:

Title: "الفوائد" or "كناشة"
New note button (+ فائدة جديدة) - compact, right-aligned
Optional: search/filter icon

Date Groups:
اليوم (Today)
  ├─ فائدة 1533
  └─ فائدة 1420

أمس (Yesterday)
  └─ فائدة 0911

هذا الأسبوع (This Week)
  ├─ فائدة ...
  └─ فائدة ...

هذا الشهر (This Month)
  └─ فائدة ...

أقدم (Older)
  └─ فائدة ...
Date Group Headers:

Font: 12px, muted color (#888)
Uppercase or small-caps styling
Sticky positioning within scroll (optional)
No collapse/expand needed - always visible

Note Items:

Height: 48px
Show: title (or first line if untitled), timestamp
Truncate long titles with ellipsis
Selected state: accent background
Hover state: subtle highlight

Note Item Layout:
┌────────────────────────────────┐
│ عنوان الفائدة أو السطر الأول... │  ← 14px, primary color
│ ١٤:٣٣                          │  ← 12px, muted color
└────────────────────────────────┘
Editor Area
Same as before:

Breadcrumb showing date context: اليوم / فائدة 1533
Title as H1
Body text: Noto Naskh Arabic, 18px, line-height 1.8
Max-width 700px centered, or full-width with 48px padding

Empty States
No notes exist:
الكناشة فارغة
أضف فائدة جديدة للبدء
[+ فائدة جديدة]
No note selected (notes exist but none open):
اختر فائدة من القائمة
أو أنشئ فائدة جديدة
Interaction

Click note → opens in editor
New note → creates with current timestamp, opens immediately
Delete → right-click context menu or trash icon on hover
Notes auto-sort by creation date (newest first within each group)

